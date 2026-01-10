from collections import defaultdict

from corptools.models.assets import CharacterAsset
from eveuniverse.models import EveRegion
from allianceauth.authentication.models import CharacterOwnership


CAPITAL_GROUP_IDS = [30, 485, 547, 659, 1538]


def get_capitals_in_blacklisted_regions(blacklisted_regions):
    """
    Returns a flat list of dicts containing:
    - CharacterOwnership object
    - Ship type
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

    assets = [
        a for a in assets
        if a.location_name
        and a.location_name.system
        and a.location_name.system.constellation.region.region_id in region_ids
    ]

    output = []

    for asset in assets:
        char_id = asset.character.character.character_id

        try:
            ownership = CharacterOwnership.objects.get(character__character_id=char_id)
        except CharacterOwnership.DoesNotExist:
            continue

        output.append({
            "ownership": ownership,
            "ship_type": asset.type_name.name,
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

        # Determine main character
        main = getattr(user.profile, "main_character", None)
        if not main:
            main = ownership.character

        if not main:
            continue

        key = main.character_id

        grouped[key]["main"] = main
        grouped[key]["alts"].append(entry)

    return list(grouped.values())
