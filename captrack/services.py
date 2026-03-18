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




# Fallback keywords to discover/identify capital ship groups when group IDs differ across schemas
_CAPITAL_GROUP_NAME_KEYWORDS = [
    "titan",
    "supercarrier",
    "carrier",
    "dreadnought",
    "lancer dreadnought",
    "force auxiliary",
    "capital industrial",
    "rorqual",
]

def _discover_capital_group_ids() -> List[int]:
    """Discover capital group IDs from the DB by group name."""
    try:
        TypeModel = CharacterAsset._meta.get_field("type_name").related_model
        GroupModel = TypeModel._meta.get_field("group").related_model
        from django.db.models import Q
    except Exception:
        return []

    try:
        pk_name = GroupModel._meta.pk.name
    except Exception:
        pk_name = "pk"

    q = Q()
    for kw in _CAPITAL_GROUP_NAME_KEYWORDS:
        q |= Q(name__icontains=kw)

    try:
        return [int(x) for x in GroupModel.objects.filter(q).values_list(pk_name, flat=True).distinct()]
    except Exception:
        return []
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


def _normalize_group_name(group_name: Optional[str]) -> str:
    return (group_name or "").strip().lower()


def _is_capital_group(group_id: Optional[int], group_name: Optional[str]) -> bool:
    """Return True if the group represents a capital class we track.

    Works across schema variants by checking:
    - canonical EVE group IDs
    - discovered group PKs from DB (name-based discovery)
    - group name keywords (fallback)
    """
    try:
        gid = int(group_id) if group_id is not None else None
    except Exception:
        gid = None

    if gid in CAPITAL_GROUP_IDS:
        return True

    # name-keyword fallback
    name = _normalize_group_name(group_name)
    if any(kw in name for kw in _CAPITAL_GROUP_NAME_KEYWORDS):
        return True

    # last resort: discovered IDs (if group PKs are not canonical)
    discovered = getattr(_is_capital_group, "_discovered_ids", None)
    if discovered is None:
        discovered = set(_discover_capital_group_ids())
        setattr(_is_capital_group, "_discovered_ids", discovered)

    return gid in discovered if gid is not None else False


def _cap_class_for_group(group_id: Optional[int], group_name: Optional[str]) -> str:
    """Return normalized class string for policy logic."""
    name = _normalize_group_name(group_name)

    # Prefer explicit name match (works even if numeric IDs are non-canonical)
    if "titan" in name or "supercarrier" in name:
        return "supercapital"
    if "lancer dreadnought" in name or ("dreadnought" in name):
        return "dreadnought"
    # order matters: check supercarrier before carrier substring
    if "force auxiliary" in name:
        return "fax"
    if "carrier" in name:
        return "carrier"
    if "capital industrial" in name or "rorqual" in name:
        return "industrial"

    # Fallback to canonical ID mapping
    return _cap_class_for_group_id(group_id)


def _risk_level_for_group(group_id: Optional[int], group_name: Optional[str]) -> str:
    """Severity classification (UI + alert styling) with name fallback."""
    name = _normalize_group_name(group_name)

    if "titan" in name or "supercarrier" in name:
        return "critical"
    if "lancer dreadnought" in name or ("dreadnought" in name):
        return "high"
    if "force auxiliary" in name:
        return "medium"
    # carrier, but avoid supercarrier (handled above)
    if "carrier" in name:
        return "medium"
    if "capital industrial" in name or "rorqual" in name:
        return "industrial"

    return _risk_level_for_group_id(group_id)


# ------------------------------------------------------------------
# Public service functions
# ------------------------------------------------------------------
def get_capitals_in_blacklisted_regions(blacklisted_regions):
    # Normalize blacklisted region IDs across schemas
    def _eve_pk(obj, *names, default=None):
        """Return the first non-None attribute from obj."""
        if obj is None:
            return default
        for n in names:
            try:
                v = getattr(obj, n)
            except Exception:
                v = None
            if v is not None:
                return v
        return default

    region_ids = []
    for r in blacklisted_regions:
        rid = _eve_pk(r, "id", "region_id", "pk")
        if rid is not None:
            region_ids.append(int(rid))

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
    )

    filtered_assets: List[CharacterAsset] = []

    for asset in assets:
        # Must have a system location to map to region
        system_obj = getattr(getattr(asset, "location_name", None), "system", None)
        if not system_obj:
            continue

        # Resolve group id robustly (SDE schemas vary)
        group_obj = getattr(asset.type_name, "group", None)
        ship_group_id = (
            getattr(asset.type_name, "group_id", None)
            or getattr(group_obj, "group_id", None)
            or getattr(group_obj, "pk", None)
        )
        try:
            ship_group_id = int(ship_group_id) if ship_group_id is not None else None
        except Exception:
            ship_group_id = None

        group_name = getattr(group_obj, "name", None)

        if not _is_capital_group(ship_group_id, group_name):
            continue

        # Resolve region id (constellation->region, or system.region)
        region_obj = None
        const_obj = getattr(system_obj, "constellation", None)
        if const_obj is not None:
            region_obj = getattr(const_obj, "region", None)
        if region_obj is None:
            region_obj = getattr(system_obj, "region", None)

        region_pk = (
            _eve_pk(region_obj, "id", "region_id", "pk")
            or _eve_pk(const_obj, "region_id")
            or _eve_pk(system_obj, "region_id")
        )
        try:
            region_pk = int(region_pk) if region_pk is not None else None
        except Exception:
            region_pk = None

        if region_pk is None or region_pk not in region_ids:
            continue

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

        group_obj = getattr(asset.type_name, "group", None)
        ship_group_id = (
            getattr(asset.type_name, "group_id", None)
            or getattr(group_obj, "group_id", None)
            or getattr(group_obj, "pk", None)
        )
        try:
            ship_group_id = int(ship_group_id) if ship_group_id is not None else None
        except Exception:
            ship_group_id = None

        ship_type_id = (
            getattr(asset.type_name, "eve_type_id", None)
            or getattr(asset.type_name, "type_id", None)
            or getattr(asset.type_name, "id", None)
            or getattr(asset.type_name, "pk", None)
        )

        group_name = getattr(group_obj, "name", None)

        alert_level = _risk_level_for_group(ship_group_id, group_name)
        cap_class = _cap_class_for_group(ship_group_id, group_name)

        system_obj = getattr(getattr(asset, "location_name", None), "system", None)
        const_obj = getattr(system_obj, "constellation", None) if system_obj else None
        region_obj = getattr(const_obj, "region", None) if const_obj else None
        if region_obj is None and system_obj is not None:
            region_obj = getattr(system_obj, "region", None)

        system_name = getattr(system_obj, "name", "(Unknown)")
        system_id = _eve_pk(system_obj, "system_id", "id", "pk")
        region_name = getattr(region_obj, "name", None) or getattr(region_obj, "region_name", None) or "(Unknown)"
        region_id = _eve_pk(region_obj, "id", "region_id", "pk") or _eve_pk(const_obj, "region_id") or _eve_pk(system_obj, "region_id")

        structure_name = getattr(getattr(asset, "location_name", None), "location_name", None) or "(Unknown)"
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
            "cap_class": cap_class,
            "risk": alert_level,
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
