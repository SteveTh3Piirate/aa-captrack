from collections import Counter
from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo
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

    # Snooze handling (single row + bulk "snooze all")
    if request.method == "POST":
        snooze_action = (request.POST.get("snooze_action") or "").lower()

        def _snooze_until(action: str):
            if action == "clear":
                return None
            if action == "1h":
                return now + timedelta(hours=1)
            if action == "6h":
                return now + timedelta(hours=6)
            if action == "24h":
                return now + timedelta(hours=24)
            # "Infinite" snooze: far-future timestamp (no migration required)
            if action in {"inf", "infinite", "forever", "∞"}:
                return now + timedelta(days=3650)  # ~10 years
            return None

        # Bulk snooze: expects comma-separated watchlist IDs
        watchlist_ids_raw = request.POST.get("watchlist_ids")
        if watchlist_ids_raw and snooze_action:
            ids = []
            for part in watchlist_ids_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    ids.append(int(part))
                except (ValueError, TypeError):
                    continue

            if ids:
                CapWatchlist.objects.filter(pk__in=ids).update(
                    alert_snoozed_until=_snooze_until(snooze_action)
                )

        # Single row snooze
        watchlist_id = request.POST.get("watchlist_id")
        if watchlist_id and snooze_action and not watchlist_ids_raw:
            try:
                wl = CapWatchlist.objects.get(pk=int(watchlist_id))
            except (CapWatchlist.DoesNotExist, ValueError, TypeError):
                wl = None

            if wl:
                wl.alert_snoozed_until = _snooze_until(snooze_action)
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

        # ------------------------------------------------------------------
        # UI helpers for the dashboard template
        # ------------------------------------------------------------------
        main = group.get("main")
        main_character_id = getattr(main, "character_id", None) or getattr(main, "pk", None)
        group["main_character_id"] = main_character_id

        # Corptools audit URL (relative; will inherit current site domain)
        if main_character_id:
            group["audit_url"] = f"/audit/r/{main_character_id}/account/overview"
        else:
            group["audit_url"] = None

        # Bulk snooze: unique watchlist ids in this card
        wl_ids = sorted({e.get("watchlist_id") for e in entries if e.get("watchlist_id")})
        group["watchlist_ids_str"] = ",".join(str(i) for i in wl_ids)

        # Corporation / alliance info (names + logo urls)
        # IMPORTANT: Don't touch Character.corporation / Character.alliance properties here.
        # Those properties can raise Eve*Info.DoesNotExist if the info tables haven't been
        # hydrated yet. Instead, query EveCorporationInfo / EveAllianceInfo with filter().first().

        corp_id = getattr(main, "corporation_id", None) or None
        if corp_id == 0:
            corp_id = None
        corp_name = getattr(main, "corporation_name", None)

        corp_obj = None
        if corp_id:
            corp_obj = EveCorporationInfo.objects.filter(corporation_id=corp_id).first()
            if corp_obj:
                corp_name = corp_name or getattr(corp_obj, "corporation_name", None) or getattr(corp_obj, "name", None)

        alliance_id = getattr(main, "alliance_id", None) or None
        if alliance_id == 0:
            alliance_id = None
        alliance_name = getattr(main, "alliance_name", None)

        alliance_obj = None
        if alliance_id:
            alliance_obj = EveAllianceInfo.objects.filter(alliance_id=alliance_id).first()
            if alliance_obj:
                alliance_name = alliance_name or getattr(alliance_obj, "alliance_name", None) or getattr(alliance_obj, "name", None)

        group["corp_id"] = corp_id
        group["corp_name"] = corp_name
        group["corp_logo_url"] = (
            f"https://images.evetech.net/corporations/{corp_id}/logo?size=32" if corp_id else None
        )
        group["alliance_id"] = alliance_id
        group["alliance_name"] = alliance_name
        group["alliance_logo_url"] = (
            f"https://images.evetech.net/alliances/{alliance_id}/logo?size=32" if alliance_id else None
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
