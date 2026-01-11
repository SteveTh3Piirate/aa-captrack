from collections import defaultdict

from corptools.models.assets import CharacterAsset
from allianceauth.authentication.models import CharacterOwnership

CAPITAL_GROUP_IDS = [
    30,    # Titans (includes faction titans)
    485,   # Supercarriers
    547,   # Carriers
    659,   # Dreadnoughts
    1972,  # Lancer Dreadnoughts
    1538,  # Force Auxiliaries
]


def get_capitals_in_blacklisted_regions(blacklisted_regions):
    """
    Returns a flat list of dicts containing:
    - CharacterOwnership object
    - Ship type name
    - Ship type ID (for Discord images)
    - System name
    - Structure/station name
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

    # Keep only assets that resolve to a region and are in the blacklist
    filtered_assets = []
    for a in assets:
        if not a.location_name or not a.location_name.system:
            continue
        region = a.location_name.system.constellation.region
        if region and region.region_id in region_ids:
            filtered_assets.append(a)

    output = []

    for asset in filtered_assets:
        # corptools CharacterAsset links: asset.character -> CharacterOwnership-ish wrapper,
        # but we follow your existing chain:
        char_id = asset.character.character.character_id

        try:
            ownership = CharacterOwnership.objects.get(character__character_id=char_id)
        except CharacterOwnership.DoesNotExist:
            continue

        # Try to extract eve type id for ship image
        ship_type_id = None
        try:
            ship_type_id = getattr(asset.type_name, "eve_type_id", None) or getattr(asset.type_name, "type_id", None)
        except Exception:
            ship_type_id = None

        output.append({
            "ownership": ownership,
            "ship_type": asset.type_name.name,
            "ship_type_id": ship_type_id,
            "system": asset.location_name.system.name,
            "structure": asset.location_name.location_name or "(Unknown)",
        })

    return output


def group_capitals_by_main(entries):
    """
    Groups capital entries by main character.
    Returns a list of dicts with:
    - main: main character object
    - alts: list of entries belonging to that main
    """
    grouped = defaultdict(lambda: {"main": None, "alts": []})

    for entry in entries:
        ownership = entry["ownership"]
        user = ownership.user

        main = getattr(user.profile, "main_character", None)
        if not main:
            main = ownership.character

        if not main:
            continue

        key = main.character_id
        grouped[key]["main"] = main
        grouped[key]["alts"].append(entry)

    return list(grouped.values())
