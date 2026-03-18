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


def _eve_pk(obj: Any, *attrs: str) -> Optional[int]:
    """Return the first usable integer-ish primary key from a list of attrs."""
    if obj is None:
        return None
    for attr in attrs:
        try:
            value = getattr(obj, attr, None)
        except Exception:
            value = None
        if value in (None, ""):
            continue
        try:
            return int(value)
        except Exception:
            continue
    return None




def _safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """getattr that swallows broken/missing related-object lookups."""
    if obj is None:
        return default
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default

def _build_sde_capital_name_map() -> Tuple[Dict[str, int], Dict[str, int]]:
    """Return maps of capital hull name -> type_id and name -> group_id using eve_sde as source of truth.

    Keys are casefolded hull names. This avoids relying on Corptools internal ids which can vary across versions.
    """
    try:
        from eve_sde.models import ItemType  # type: ignore
    except Exception:
        return {}, {}

    try:
        qs = ItemType.objects.filter(group_id__in=CAPITAL_GROUP_IDS).values_list("id", "name", "group_id")
    except Exception:
        return {}, {}

    name_to_type: Dict[str, int] = {}
    name_to_group: Dict[str, int] = {}
    for type_id, name, group_id in qs:
        if not name:
            continue
        key = str(name).casefold()
        try:
            name_to_type[key] = int(type_id)
        except Exception:
            continue
        try:
            name_to_group[key] = int(group_id)
        except Exception:
            name_to_group[key] = 0
    return name_to_type, name_to_group


def _resolve_asset_hull_name(asset: "CharacterAsset") -> Optional[str]:
    """Best-effort resolve hull name for an asset across Corptools schema variants."""
    t = getattr(asset, "type_name", None)
    candidates: List[Any] = []
    if t is not None:
        candidates.extend([
            getattr(t, "name", None),
            getattr(t, "type_name", None),
            getattr(t, "item_name", None),
        ])
        try:
            eit = getattr(t, "eveitemtype", None)
        except Exception:
            eit = None
        if eit is not None:
            candidates.extend([
                getattr(eit, "name", None),
                getattr(eit, "type_name", None),
                getattr(eit, "item_name", None),
            ])
    for c in candidates:
        if c:
            return str(c)
    return None


def _resolve_ship_type_id(asset: "CharacterAsset") -> Optional[int]:
    """Best-effort resolve EVE ship type id across Corptools schema variants."""
    t = getattr(asset, "type_name", None)
    candidates = [
        getattr(asset, "type_id", None),
        getattr(t, "type_id", None),
        getattr(t, "id", None),
    ]
    try:
        eit = getattr(t, "eveitemtype", None)
    except Exception:
        eit = None
    if eit is not None:
        candidates.extend([
            getattr(eit, "type_id", None),
            getattr(eit, "id", None),
        ])

    for value in candidates:
        if value in (None, ""):
            continue
        try:
            return int(value)
        except Exception:
            continue
    return None


def _resolve_system_id(asset: "CharacterAsset") -> Optional[int]:
    """Best-effort resolve solar system id across Corptools schema variants."""
    location = _safe_getattr(asset, "location_name", None)
    system = _safe_getattr(location, "system", None) if location is not None else None

    candidates = [
        getattr(asset, "system_id", None),
        getattr(location, "system_id", None) if location is not None else None,
        getattr(system, "system_id", None) if system is not None else None,
        getattr(system, "id", None) if system is not None else None,
        getattr(system, "pk", None) if system is not None else None,
    ]
    for value in candidates:
        if value in (None, ""):
            continue
        try:
            return int(value)
        except Exception:
            continue
    return None


def _resolve_region_info(asset: "CharacterAsset") -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """Return (region_id, region_name, system_name) across Corptools/EVE SDE schema variants."""
    location = _safe_getattr(asset, "location_name", None)
    system = _safe_getattr(location, "system", None) if location is not None else None
    constellation = getattr(system, "constellation", None) if system is not None else None
    region = getattr(constellation, "region", None) if constellation is not None else None

    region_id = _eve_pk(region, "region_id", "id", "pk")
    region_name = getattr(region, "name", None)
    system_name = getattr(system, "name", None)

    if region_id is not None:
        return region_id, region_name, system_name

    system_id = _resolve_system_id(asset)
    if system_id is None:
        return None, None, system_name

    try:
        from eve_sde.models import SolarSystem  # type: ignore
    except Exception:
        return None, None, system_name

    try:
        s = (
            SolarSystem.objects
            .select_related("constellation__region")
            .filter(system_id=system_id)
            .first()
        )
    except Exception:
        s = None

    if not s:
        return None, None, system_name

    try:
        region_obj = s.constellation.region
    except Exception:
        region_obj = None

    return (
        _eve_pk(region_obj, "region_id", "id", "pk"),
        getattr(region_obj, "name", None),
        getattr(s, "name", None) or system_name,
    )


# ------------------------------------------------------------------
# Classification helpers
# ------------------------------------------------------------------
def _cap_class_for_group_id(group_id: Optional[int]) -> str:
    """Returns a normalized capital class string for policy logic."""
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
    """Severity classification (UI + alert styling)."""
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
    """Default alertability (overridden later by policy logic)."""
    return alert_level in {"critical", "high", "medium"}


# ------------------------------------------------------------------
# Public service functions
# ------------------------------------------------------------------
def get_capitals_in_blacklisted_regions(blacklisted_regions: Sequence[Any]) -> List[Dict[str, Any]]:
    """Return capital assets located in the given blacklisted regions.

    Robust across Corptools 3.x schema variants by:
    - resolving regions via eve_sde (fallbacks when Corptools map tables are incomplete)
    - classifying capitals using eve_sde ItemType group_id by hull name (not Corptools internal ids)
    """
    region_ids: List[int] = []
    for r in blacklisted_regions:
        rid = _eve_pk(r, "id", "region_id", "pk")
        if rid is None:
            continue
        try:
            region_ids.append(int(rid))
        except Exception:
            continue

    if not region_ids:
        return []

    cap_name_to_type_id, cap_name_to_group_id = _build_sde_capital_name_map()

    assets = (
        CharacterAsset.objects
        .select_related(
            "character",
            "character__character",
            "type_name",
            "location_name",
        )
        .all()
    )

    output: List[Dict[str, Any]] = []

    for asset in assets:
        region_id, region_name, system_name_fallback = _resolve_region_info(asset)
        if region_id is None:
            continue
        try:
            region_id_int = int(region_id)
        except Exception:
            continue
        if region_id_int not in region_ids:
            continue

        hull_name = _resolve_asset_hull_name(asset) or getattr(getattr(asset, "type_name", None), "name", None)
        if not hull_name:
            continue
        key = str(hull_name).casefold()

        ship_group_id = cap_name_to_group_id.get(key)
        if ship_group_id not in CAPITAL_GROUP_IDS:
            continue

        ship_type_id_int = cap_name_to_type_id.get(key) or _resolve_ship_type_id(asset)

        # resolve character id
        char_id = None
        try:
            char_id = asset.character.character.character_id
        except Exception:
            try:
                char_id = asset.character.character_id
            except Exception:
                char_id = None
        if char_id is None:
            continue

        try:
            ownership = CharacterOwnership.objects.get(character__character_id=char_id)
        except CharacterOwnership.DoesNotExist:
            continue

        alert_level = _risk_level_for_group_id(ship_group_id)
        cap_class = _cap_class_for_group_id(ship_group_id)

        try:
            system_obj = getattr(getattr(asset, "location_name", None), "system", None)
        except Exception:
            system_obj = None
        system_id = _eve_pk(system_obj, "system_id", "id", "pk") or _resolve_system_id(asset)

        system_name = getattr(system_obj, "name", None) or system_name_fallback or "(Unknown)"
        region_name = region_name or "(Unknown)"

        structure_name = getattr(getattr(asset, "location_name", None), "location_name", None) or "(Unknown)"
        location_str = f"{region_name} → {system_name}"

        output.append({
            "ownership": ownership,
            "character_id": char_id,
            "character_name": getattr(ownership.character, "character_name", str(char_id)),
            "ship_type": str(hull_name),
            "ship_type_id": ship_type_id_int,
            "ship_group_id": ship_group_id,
            "cap_class": cap_class,
            "risk": alert_level,
            "alert_level": alert_level,
            "should_alert": _should_alert(alert_level),
            "region": region_name,
            "region_id": region_id_int,
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
