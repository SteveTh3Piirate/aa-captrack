from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from django.utils import timezone

from corptools.models.assets import CharacterAsset
from allianceauth.authentication.models import CharacterOwnership

from .models import CapWatchlist

# NOTE:
# Group IDs cover T1 + faction variants within the same group.
CAPITAL_GROUP_IDS: List[int] = [
    30,    # Titans (includes faction titans)
    659,   # Supercarriers (includes faction dreads)
    1972,  # Lancer Dreadnoughts
    485,   # Dreadnaughts
    1538,  # Force Auxiliaries
    547,   # Carriers
    883,   # Capital Industrial Ships (Rorqual)
]


def _risk_level_for_group_id(group_id: Optional[int]) -> str:
    """
    Alert classification policy:

    - critical: Titans, Supercarriers
    - high: Dreadnoughts, Lancer Dreadnoughts
    - medium: Carriers, Force Auxiliaries
    - industrial: Capital Industrial Ships (Rorqual)
    """
    if group_id in (30, 659):          # Titans, Supercarriers
        return "critical"
    if group_id in (485, 1972):        # Dreadnoughts, Lancer Dreads
        return "high"
    if group_id in (547, 1538):        # Carriers, FAX
        return "medium"
    if group_id == 883:                # Rorqual
        return "industrial"
    return "unknown"


def _should_alert(alert_level: str) -> bool:
    """
    Whether this capital should generate alerts.

    Industrial ships are tracked but do not alert by default.
    """
    return alert_level in {"critical", "high", "medium"}


def get_capitals_in_blacklisted_regions(blacklisted_regions):
    """
    Returns a flat list of dicts containing:
    - CharacterOwnership object (ownership)
    - Character ID + name
    - Ship type name, type ID, group ID
    - Alert level + should_alert
    - Region/system + IDs
    - Structure/station name
    - Human breadcrumb "Region → System"
    """
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
    for a in assets:
        if not a.location_name or not a.location_name.system:
            continue
        region = a.location_name.system.constellation.region
        if region and region.region_id in region_ids:
            filtered_assets.append(a)

    output: List[Dict[str, Any]] = []

    for asset in filtered_assets:
        char_id = asset.character.character.character_id

        try:
            ownership = CharacterOwnership.objects.get(
                character__character_id=char_id
            )
        except CharacterOwnership.DoesNotExist:
            continue

        ship_type_id = (
            getattr(asset.type_name, "eve_type_id", None)
            or getattr(asset.type_name, "type_id", None)
        )
        ship_group_id = getattr(asset.type_name.group, "group_id", None)

        alert_level = _risk_level_for_group_id(ship_group_id)

        system_obj = asset.location_name.system
        region_obj = (
            system_obj.constellation.region
            if system_obj and system_obj.constellation
            else None
        )

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
            "risk": alert_level,            # backward compat
            "alert_level": alert_level,     # explicit
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
