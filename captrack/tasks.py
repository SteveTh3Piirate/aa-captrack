from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import CapTrackSettings, CapWatchlist
from .services import get_capitals_in_blacklisted_regions, group_capitals_by_main
from .utils.discord import build_captrack_main_embed, send_discord_webhook


DEFAULT_COOLDOWN_MINUTES = 360
DEFAULT_CRITICAL_MIN_REPEAT_MINUTES = 15


def _get_character_id_from_ownership(ownership) -> int | None:
    ch = getattr(ownership, "character", None)
    if ch is not None:
        cid = getattr(ch, "character_id", None)
        if cid:
            return cid
        inner = getattr(ch, "character", None)
        if inner is not None:
            return getattr(inner, "character_id", None)
    return None


def _safe_dashboard_url() -> str | None:
    base = getattr(settings, "SITE_URL", "") or ""
    if not base:
        return None
    try:
        path = reverse("captrack:dashboard")
    except Exception:
        return None
    return base.rstrip("/") + path


@shared_task
def scan_capitals_and_send_alerts():
    """
    Scheduled task:
    - Scans for capitals in blacklisted regions (service output includes alert_level + should_alert)
    - Updates watchlist last_seen
    - Sends consolidated Discord alerts (one embed per main)

    Rules:
    - Snooze always suppresses alerts
    - Industrial is tracked but does not alert (services: should_alert=False)
    - Critical ignores normal cooldown but has a minimum repeat interval (spam guard)
    - High/Medium use normal cooldown
    """
    settings_obj = CapTrackSettings.objects.first()
    if not settings_obj or not settings_obj.webhook_url:
        return

    cooldown_minutes = getattr(
        settings, "CAPTRACK_ALERT_COOLDOWN_MINUTES", DEFAULT_COOLDOWN_MINUTES
    )
    cooldown_delta = timedelta(minutes=cooldown_minutes)

    critical_repeat_minutes = getattr(
        settings,
        "CAPTRACK_CRITICAL_MIN_REPEAT_MINUTES",
        DEFAULT_CRITICAL_MIN_REPEAT_MINUTES,
    )
    critical_repeat_delta = timedelta(minutes=critical_repeat_minutes)

    blacklisted = settings_obj.blacklisted_regions.all()
    results = get_capitals_in_blacklisted_regions(blacklisted)
    now = timezone.now()

    # Track which character IDs are currently detected (for cleanup)
    detected_ids: set[int] = set()
    ownership_ids: set[int] = set()

    for r in results:
        ownership = r.get("ownership")
        if not ownership:
            continue
        ownership_ids.add(ownership.pk)

        cid = r.get("character_id") or _get_character_id_from_ownership(ownership)
        if cid:
            detected_ids.add(cid)

    # Ensure watchlist rows exist for detected ownerships; update last_seen
    # (single write per detected ownership)
    for r in results:
        ownership = r.get("ownership")
        if not ownership:
            continue

        CapWatchlist.objects.update_or_create(
            character=ownership,
            defaults={"last_seen": now},
        )

    # Load watchlist rows for quick snooze/cooldown checks
    watchlists = {
        wl.character_id: wl
        for wl in CapWatchlist.objects.filter(character_id__in=ownership_ids)
        .select_related("character")
    }

    dashboard_url = _safe_dashboard_url()

    # Consolidate by main
    groups = group_capitals_by_main(results)

    for group in groups:
        main = group.get("main")
        entries = group.get("alts") or []
        if not main or not entries:
            continue

        # Determine which entries should trigger an alert this run
        eligible_watchlists: dict[int, CapWatchlist] = {}
        snoozed_lines: list[str] = []

        for e in entries:
            ownership = e.get("ownership")
            if not ownership:
                continue

            wl = watchlists.get(ownership.pk)
            if not wl:
                continue

            alert_level = e.get("alert_level") or e.get("risk") or "unknown"
            should_alert = bool(e.get("should_alert", False))
            if not should_alert:
                continue

            # Snooze always wins
            if wl.alert_snoozed_until and wl.alert_snoozed_until > now:
                until = wl.alert_snoozed_until.strftime("%Y-%m-%d %H:%M")
                snoozed_lines.append(
                    f"**{e.get('character_name', 'Unknown')}** until {until} (UTC)"
                )
                continue

            # Cooldown rules
            if alert_level == "critical":
                # Spam guard only (still "always alert" in the sense of no long cooldown)
                if wl.last_alert_sent and (now - wl.last_alert_sent) < critical_repeat_delta:
                    continue
            else:
                if wl.last_alert_sent and (now - wl.last_alert_sent) < cooldown_delta:
                    continue

            eligible_watchlists[wl.pk] = wl

        if not eligible_watchlists:
            continue

        # Build consolidated embed (includes ALL entries for context)
        # but still shows snoozed list separately
        main_id = getattr(main, "character_id", None) or getattr(main, "pk", None) or 0
        main_name = getattr(main, "character_name", str(main))

        status_line = (
            f"Consolidated alert • cooldown {cooldown_minutes}m • "
            f"critical min repeat {critical_repeat_minutes}m"
        )

        embed = build_captrack_main_embed(
            main_character_id=int(main_id) if main_id else 0,
            main_character_name=main_name,
            entries=entries,
            dashboard_url=dashboard_url,
            snoozed_lines=snoozed_lines,
            status_line=status_line,
        )

        sent = send_discord_webhook(settings_obj.webhook_url, embeds=[embed])
        if sent:
            # Update last_alert_sent only for entries that were eligible this run
            CapWatchlist.objects.filter(pk__in=list(eligible_watchlists.keys())).update(
                last_alert_sent=now
            )

    # Cleanup watchlist entries no longer detected
    to_remove: list[int] = []
    for wl in CapWatchlist.objects.select_related("character").all():
        wl_char_id = _get_character_id_from_ownership(wl.character)
        if wl_char_id and wl_char_id not in detected_ids:
            to_remove.append(wl.pk)

    if to_remove:
        CapWatchlist.objects.filter(pk__in=to_remove).delete()


@shared_task
def refresh_watchlist_assets():
    """
    Periodic task:
    - Refresh assets only for characters currently on watchlist
    """
    from corptools.tasks import update_subset_of_characters

    char_ids: list[int] = []
    for wl in CapWatchlist.objects.select_related("character"):
        cid = _get_character_id_from_ownership(wl.character)
        if cid:
            char_ids.append(cid)

    if char_ids:
        update_subset_of_characters.apply_async(kwargs={"character_ids": char_ids})
