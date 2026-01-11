from collections import Counter
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import CapTrackSettings, CapWatchlist
from .services import get_capitals_in_blacklisted_regions, group_capitals_by_main
from .utils.discord import build_captrack_main_embed, send_discord_webhook


ALWAYS_ALERT_GROUP_IDS = {30, 659}
THRESHOLD_GROUP_IDS = {485, 1972, 547, 1538}
ALERT_THRESHOLD = 5

DEFAULT_COOLDOWN_MINUTES = 360
DEFAULT_CRITICAL_MIN_REPEAT_MINUTES = 15


def _safe_dashboard_url():
    base = getattr(settings, "SITE_URL", "") or ""
    if not base:
        return None
    try:
        return base.rstrip("/") + reverse("captrack:dashboard")
    except Exception:
        return None


@shared_task
def scan_capitals_and_send_alerts():
    settings_obj = CapTrackSettings.objects.first()
    if not settings_obj or not settings_obj.webhook_url:
        return

    cooldown = timedelta(minutes=getattr(settings, "CAPTRACK_ALERT_COOLDOWN_MINUTES", DEFAULT_COOLDOWN_MINUTES))
    crit_repeat = timedelta(minutes=getattr(settings, "CAPTRACK_CRITICAL_MIN_REPEAT_MINUTES", DEFAULT_CRITICAL_MIN_REPEAT_MINUTES))

    now = timezone.now()
    results = get_capitals_in_blacklisted_regions(settings_obj.blacklisted_regions.all())
    groups = group_capitals_by_main(results)
    dashboard_url = _safe_dashboard_url()

    for group in groups:
        entries = group.get("alts") or []
        counts = Counter(e.get("ship_group_id") for e in entries)

        eligible = {}
        snoozed = []

        for e in entries:
            gid = e.get("ship_group_id")
            ownership = e.get("ownership")
            if not ownership:
                continue

            wl, _ = CapWatchlist.objects.update_or_create(
                character=ownership,
                defaults={"last_seen": now},
            )

            if wl.alert_snoozed_until and wl.alert_snoozed_until > now:
                snoozed.append(e.get("character_name"))
                continue

            if gid in ALWAYS_ALERT_GROUP_IDS:
                pass
            elif gid in THRESHOLD_GROUP_IDS:
                if counts.get(gid, 0) < ALERT_THRESHOLD:
                    continue
            else:
                continue

            if wl.last_alert_sent:
                delta = now - wl.last_alert_sent
                if e.get("alert_level") == "critical":
                    if delta < crit_repeat:
                        continue
                elif delta < cooldown:
                    continue

            eligible[wl.pk] = wl

        if not eligible:
            continue

        embed = build_captrack_main_embed(
            main_character_id=group["main"].character_id,
            main_character_name=group["main"].character_name,
            entries=entries,
            dashboard_url=dashboard_url,
            snoozed_lines=snoozed,
        )

        if send_discord_webhook(settings_obj.webhook_url, embeds=[embed]):
            CapWatchlist.objects.filter(pk__in=eligible.keys()).update(last_alert_sent=now)
