from collections import Counter
from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from .constants import CAPTRACK_BASIC_ACCESS_PERM
from .models import CapTrackSettings, CapWatchlist
from .services import get_capitals_in_blacklisted_regions, group_capitals_by_main


ALWAYS_ALERT_GROUP_IDS = {30, 659}            # Titan, Supercarrier
THRESHOLD_GROUP_IDS = {485, 1972, 547, 1538}  # Dread, Lancer, Carrier, FAX
ALERT_THRESHOLD = 5


def _level_rank(level: str) -> int:
    return {
        "critical": 5,
        "high": 4,
        "medium": 3,
        "low": 2,
        "industrial": 1,
        "unknown": 0,
        None: 0,
    }.get((level or "unknown").lower(), 0)


def _supercap_priority(ship_group_id) -> int:
    if ship_group_id == 30:
        return 2
    if ship_group_id == 659:
        return 1
    return 0


@login_required
@permission_required(CAPTRACK_BASIC_ACCESS_PERM, raise_exception=True)
def dashboard(request):
    now = timezone.now()

    # Snooze handling (unchanged)
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
                wl.save(update_fields=["alert_snoozed_until"])

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
        entry.update({
            "watchlist_id": wl.pk,
            "last_seen": wl.last_seen,
            "last_alert_sent": wl.last_alert_sent,
            "alert_snoozed_until": wl.alert_snoozed_until,
            "is_snoozed": wl.alert_snoozed_until and wl.alert_snoozed_until > now,
        })

    groups = group_capitals_by_main(raw_entries)

    for group in groups:
        entries = group.get("alts", [])
        counts = Counter(e.get("ship_group_id") for e in entries)

        # Apply the "always alert" + "threshold alert" policy
        for e in entries:
            gid = e.get("ship_group_id")

            if gid in ALWAYS_ALERT_GROUP_IDS:
                e["should_alert"] = True
            elif gid in THRESHOLD_GROUP_IDS:
                e["should_alert"] = counts.get(gid, 0) >= ALERT_THRESHOLD
            else:
                e["should_alert"] = False

        # Sort within each main: severity -> Titan>Super priority -> name
        entries.sort(
            key=lambda e: (
                -_level_rank(e.get("alert_level")),
                -_supercap_priority(e.get("ship_group_id")),
                (e.get("character_name") or "").lower(),
            )
        )

        group["alts"] = entries
        group["total_capitals"] = len(entries)
        group["alerting_capitals"] = sum(1 for e in entries if e.get("should_alert"))
        group["is_alerting"] = group["alerting_capitals"] > 0

        # IMPORTANT FIX:
        # Badge should represent what's present, not only what is currently alerting.
        all_levels = {e.get("alert_level") for e in entries if e.get("alert_level")}
        group["max_alert_level"] = (
            "critical" if "critical" in all_levels else
            "high" if "high" in all_levels else
            "medium" if "medium" in all_levels else
            "low" if "low" in all_levels else
            "industrial" if "industrial" in all_levels else
            "unknown"
        )

    groups.sort(
        key=lambda g: (
            -_level_rank(g.get("max_alert_level")),
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
