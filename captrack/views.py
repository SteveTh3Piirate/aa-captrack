from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from .constants import CAPTRACK_BASIC_ACCESS_PERM
from .models import CapTrackSettings, CapWatchlist
from .services import get_capitals_in_blacklisted_regions, group_capitals_by_main


def _level_rank(level: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "industrial": 1, "unknown": 0}.get(level or "unknown", 0)


@login_required
@permission_required(CAPTRACK_BASIC_ACCESS_PERM, raise_exception=True)
def dashboard(request):
    now = timezone.now()

    # -----------------------------
    # Handle snooze actions (POST)
    # -----------------------------
    if request.method == "POST":
        watchlist_id = request.POST.get("watchlist_id")
        snooze_action = request.POST.get("snooze_action")

        if watchlist_id and snooze_action:
            try:
                wl = CapWatchlist.objects.get(pk=int(watchlist_id))
            except (CapWatchlist.DoesNotExist, ValueError, TypeError):
                wl = None

            if wl:
                if snooze_action == "clear":
                    wl.alert_snoozed_until = None
                elif snooze_action == "1h":
                    wl.alert_snoozed_until = now + timedelta(hours=1)
                elif snooze_action == "6h":
                    wl.alert_snoozed_until = now + timedelta(hours=6)
                elif snooze_action == "24h":
                    wl.alert_snoozed_until = now + timedelta(hours=24)
                else:
                    wl = None

                if wl:
                    wl.save(update_fields=["alert_snoozed_until"])

    # -----------------------------
    # Build dashboard context
    # -----------------------------
    settings = CapTrackSettings.objects.first()
    blacklisted_regions = settings.blacklisted_regions.all() if settings else []

    raw_entries = get_capitals_in_blacklisted_regions(blacklisted_regions)

    watchlist_by_ownership_id = {
        wl.character_id: wl
        for wl in CapWatchlist.objects.select_related("character").all()
    }

    for entry in raw_entries:
        ownership = entry.get("ownership")
        if not ownership:
            continue

        wl = watchlist_by_ownership_id.get(ownership.pk)
        if not wl:
            continue

        entry["watchlist_id"] = wl.pk
        entry["last_seen"] = wl.last_seen
        entry["last_alert_sent"] = wl.last_alert_sent
        entry["alert_snoozed_until"] = wl.alert_snoozed_until
        entry["is_snoozed"] = wl.alert_snoozed_until is not None and wl.alert_snoozed_until > now

    groups = group_capitals_by_main(raw_entries)

    for group in groups:
        entries = group.get("alts", [])
        levels = {e.get("alert_level") for e in entries}
        if "critical" in levels:
            group["max_alert_level"] = "critical"
        elif "high" in levels:
            group["max_alert_level"] = "high"
        elif "medium" in levels:
            group["max_alert_level"] = "medium"
        elif "industrial" in levels:
            group["max_alert_level"] = "industrial"
        else:
            group["max_alert_level"] = "unknown"

        group["total_capitals"] = len(entries)
        group["alerting_capitals"] = sum(1 for e in entries if e.get("should_alert"))

    # Sort: highest severity first, then by main name for stability
    groups.sort(
        key=lambda g: (
            -_level_rank(g.get("max_alert_level", "unknown")),
            (getattr(g.get("main"), "character_name", "") or "").lower(),
        )
    )

    return render(
        request,
        "captrack/dashboard.html",
        {
            "blacklisted_regions": blacklisted_regions,
            "groups": groups,
            "now": now,
        },
    )
