from __future__ import annotations

from collections import Counter
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import CapTrackSettings, CapWatchlist
from .services import get_capitals_in_blacklisted_regions, group_capitals_by_main
from .utils.discord import build_captrack_main_embed, send_discord_webhook, build_discord_mentions


# -----------------------------
# Alert policy (per main)
# -----------------------------
# Always alert (supercapitals)
ALWAYS_ALERT_GROUP_IDS = {30, 659}  # Titan, Supercarrier
# Alert only if >= threshold of the same class under the same main
THRESHOLD_GROUP_IDS = {485, 1972, 547, 1538}  # Dread, Lancer Dread, Carrier, FAX
DEFAULT_SUBCAP_ALERT_THRESHOLD = 5

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
    - Scans for capitals in blacklisted regions (services output includes ship_group_id + alert_level)
    - Updates watchlist last_seen
    - Sends consolidated Discord alerts (one embed per main)

    Rules:
    - Snooze always suppresses alerts
    - Titans/Supers always alert
    - Dreads/Lancers/Carriers/FAX only alert if >= threshold under the same main
    - Industrial is tracked only
    - Critical ignores normal cooldown but has a minimum repeat interval (spam guard)
    - High/Medium use normal cooldown
    - Discord embed lists ONLY what is actually alerting (dashboard truth)
    """
    settings_obj = CapTrackSettings.objects.first()
    if not settings_obj or not settings_obj.webhook_url:
        return

    cooldown_minutes = getattr(settings, "CAPTRACK_ALERT_COOLDOWN_MINUTES", DEFAULT_COOLDOWN_MINUTES)
    cooldown_delta = timedelta(minutes=cooldown_minutes)

    critical_repeat_minutes = getattr(
        settings, "CAPTRACK_CRITICAL_MIN_REPEAT_MINUTES", DEFAULT_CRITICAL_MIN_REPEAT_MINUTES
    )
    critical_repeat_delta = timedelta(minutes=critical_repeat_minutes)

    threshold = getattr(settings, "CAPTRACK_SUBCAP_ALERT_THRESHOLD", DEFAULT_SUBCAP_ALERT_THRESHOLD)

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

    # Ensure watchlist rows exist for detected ownerships; update last_seen (single write)
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
        for wl in CapWatchlist.objects.filter(character_id__in=ownership_ids).select_related("character")
    }

    dashboard_url = _safe_dashboard_url()

    # Consolidate by main
    groups = group_capitals_by_main(results)

    for group in groups:
        main = group.get("main")
        entries = group.get("alts") or []
        if not main or not entries:
            continue

        # Count thresholded ship classes under this main
        counts = Counter(
            e.get("ship_group_id") for e in entries if e.get("ship_group_id") in THRESHOLD_GROUP_IDS
        )

        eligible_watchlists: dict[int, CapWatchlist] = {}
        snoozed_lines: list[str] = []
        alert_entries: list[dict] = []

        for e in entries:
            ownership = e.get("ownership")
            if not ownership:
                continue

            wl = watchlists.get(ownership.pk)
            if not wl:
                continue

            gid = e.get("ship_group_id")
            alert_level = e.get("alert_level") or e.get("risk") or "unknown"

            # Apply policy: determine whether this entry is "alerting"
            policy_alerting = False
            if gid in ALWAYS_ALERT_GROUP_IDS:
                policy_alerting = True
            elif gid in THRESHOLD_GROUP_IDS:
                policy_alerting = counts.get(gid, 0) >= threshold

            if not policy_alerting:
                continue

            # Snooze always wins
            if wl.alert_snoozed_until and wl.alert_snoozed_until > now:
                until = wl.alert_snoozed_until.strftime("%Y-%m-%d %H:%M")
                snoozed_lines.append(f"**{e.get('character_name','Unknown')}** until {until} (UTC)")
                continue

            # Cooldown rules
            if alert_level == "critical":
                if wl.last_alert_sent and (now - wl.last_alert_sent) < critical_repeat_delta:
                    continue
            else:
                if wl.last_alert_sent and (now - wl.last_alert_sent) < cooldown_delta:
                    continue

            eligible_watchlists[wl.pk] = wl
            alert_entries.append(e)

        if not eligible_watchlists or not alert_entries:
            continue

        main_id = getattr(main, "character_id", None) or getattr(main, "pk", None) or 0
        main_name = getattr(main, "character_name", str(main))

        status_line = (
            f"Alerting entries only • threshold {threshold}+ • "
            f"cooldown {cooldown_minutes}m • critical min repeat {critical_repeat_minutes}m"
        )

        embed = build_captrack_main_embed(
            main_character_id=int(main_id) if main_id else 0,
            main_character_name=main_name,
            entries=alert_entries,  # IMPORTANT: only what is alerting
            dashboard_url=dashboard_url,
            snoozed_lines=snoozed_lines,
            status_line=status_line,
        )

        mention_text, allowed_mentions = build_discord_mentions(
            roles_csv=getattr(settings_obj, "discord_mention_roles", ""),
            users_csv=getattr(settings_obj, "discord_mention_users", ""),
        )

        # If configured, we prefix the alert with the desired mentions.
        content = mention_text if mention_text else None

        sent = send_discord_webhook(
            settings_obj.webhook_url,
            content=content,
            embeds=[embed],
            allowed_mentions=allowed_mentions,
        )
        if sent:
            CapWatchlist.objects.filter(pk__in=list(eligible_watchlists.keys())).update(last_alert_sent=now)

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
