from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from django.utils import timezone

from corptools.models.assets import CharacterAsset
from allianceauth.authentication.models import CharacterOwnership

from .models import CapWatchlist

# Capital ship group IDs (T1 + faction variants live in same groups)
CAPITAL_GROUP_IDS: List[int] = [
    30,    # Titans
    659,   # Supercarriers
    547,   # Carriers
    485,   # Dreadnoughts
    1972,  # Lancer Dreadnoughts
    1538,  # Force Auxiliaries
    883,   # Capital Industrial Ships (Rorqual)
]


# ------------------------------------------------------------------
# Classification helpers
# ------------------------------------------------------------------
def _cap_class_for_group_id(group_id: Optional[int]) -> str:
    """
    Returns a normalized capital class string for policy logic.
    """
    if group_id in (30, 659):
        return "supercapital"
    if group_id in (485, 1972):
        return "dreadnought"
    if group_id == 547:
        return "carrier"
    if group_id == 1538:
        return "fax"
    if group_id == 883:
        return "industrial"
    return "unknown"


def _risk_level_for_group_id(group_id: Optional[int]) -> str:
    """
    Severity classification (UI + alert styling).

    - critical: Titans, Supercarriers
    - high: Dreadnoughts, Lancer Dreadnoughts
    - medium: Carriers, Force Auxiliaries
    - industrial: Capital Industrials
    """
    if group_id in (30, 659):
        return "critical"
    if group_id in (485, 1972):
        return "high"
    if group_id in (547, 1538):
        return "medium"
    if group_id == 883:
        return "industrial"
    return "unknown"


def _should_alert(alert_level: str) -> bool:
    """
    Default alertability (overridden later by policy logic).
    """
    return alert_level in {"critical", "high", "medium"}


# ------------------------------------------------------------------
# Public service functions
# ------------------------------------------------------------------
def get_capitals_in_blacklisted_regions(blacklisted_regions):
    region_ids = [r.id for r in blacklisted_regions]

    assets = (
        CharacterAsset.objects
        .select_related(
            "character",
            "character__character",
            "type_name",
            "type_name__group",
            "location_name",
            "location_name__system",
            "location_name__system__constellation",
            "location_name__system__constellation__region",
        )
        .filter(type_name__group__group_id__in=CAPITAL_GROUP_IDS)
    )

    filtered_assets: List[CharacterAsset] = []
    for asset in assets:
        if not asset.location_name or not asset.location_name.system:
            continue

        region = asset.location_name.system.constellation.region
        if region and region.region_id in region_ids:
            filtered_assets.append(asset)

    output: List[Dict[str, Any]] = []

    for asset in filtered_assets:
        char_id = asset.character.character.character_id

        try:
            ownership = CharacterOwnership.objects.get(
                character__character_id=char_id
            )
        except CharacterOwnership.DoesNotExist:
            continue

        ship_group_id = getattr(asset.type_name.group, "group_id", None)
        ship_type_id = (
            getattr(asset.type_name, "eve_type_id", None)
            or getattr(asset.type_name, "type_id", None)
        )

        alert_level = _risk_level_for_group_id(ship_group_id)
        cap_class = _cap_class_for_group_id(ship_group_id)

        system_obj = asset.location_name.system
        region_obj = system_obj.constellation.region if system_obj else None

        system_name = getattr(system_obj, "name", "(Unknown)")
        system_id = getattr(system_obj, "system_id", None)
        region_name = getattr(region_obj, "name", "(Unknown)")
        region_id = getattr(region_obj, "region_id", None)

        structure_name = asset.location_name.location_name or "(Unknown)"
        location_str = f"{region_name} → {system_name}"

        output.append({
            "ownership": ownership,
            "character_id": char_id,
            "character_name": getattr(
                ownership.character, "character_name", str(char_id)
            ),
            "ship_type": asset.type_name.name,
            "ship_type_id": ship_type_id,
            "ship_group_id": ship_group_id,
            "cap_class": cap_class,               # 👈 NEW
            "risk": alert_level,                  # backward compat
            "alert_level": alert_level,
            "should_alert": _should_alert(alert_level),
            "region": region_name,
            "region_id": region_id,
            "system": system_name,
            "system_id": system_id,
            "structure": structure_name,
            "location": location_str,
        })

    return output


def touch_watchlist_last_seen(
    entries: Sequence[Dict[str, Any]], now=None
) -> Tuple[int, int]:
    if now is None:
        now = timezone.now()

    ownerships: Dict[int, CharacterOwnership] = {}
    for e in entries:
        o = e.get("ownership")
        if o:
            ownerships[o.pk] = o

    created = 0
    updated = 0

    for ownership in ownerships.values():
        obj, was_created = CapWatchlist.objects.get_or_create(
            character=ownership,
            defaults={"last_seen": now},
        )
        if was_created:
            created += 1
            continue

        if obj.last_seen is None or obj.last_seen < now:
            obj.last_seen = now
            obj.save(update_fields=["last_seen"])
            updated += 1

    return created, updated


def group_capitals_by_main(entries):
    grouped = defaultdict(lambda: {"main": None, "alts": []})

    for entry in entries:
        ownership = entry["ownership"]
        user = ownership.user

        main = getattr(user.profile, "main_character", None)
        if not main:
            main = ownership.character

        key = getattr(main, "character_id", main.pk)
        grouped[key]["main"] = main
        grouped[key]["alts"].append(entry)

    return list(grouped.values())
