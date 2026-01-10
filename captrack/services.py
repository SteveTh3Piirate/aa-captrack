from collections import defaultdict

from corptools.models.assets import CharacterAsset
from eveuniverse.models import EveRegion
from allianceauth.eveonline.models import EveCharacter


CAPITAL_GROUP_IDS = [30, 485, 547, 659, 1538]


def get_capitals_in_blacklisted_regions(blacklisted_regions):
    """
    Returns a list of EveCharacter model objects representing characters
    who have capital ships located in blacklisted regions.
    """

    # Convert to IDs for faster filtering
    region_ids = [r.id for r in blacklisted_regions]

    # Get all character assets that are capital ships
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

    # Filter to only assets located in blacklisted regions
    assets = [
        a for a in assets
        if a.location_name
        and a.location_name.system
        and a.location_name.system.constellation.region.id in region_ids
    ]

    violating_characters = []

    for asset in assets:
        # Extract the character_id from the Corptools asset
        char_id = asset.character.character.character_id

        try:
            # Convert to a real AA EveCharacter model instance
            char_obj = EveCharacter.objects.get(character_id=char_id)
            violating_characters.append(char_obj)
        except EveCharacter.DoesNotExist:
            # Skip characters not linked in AA
            continue

    return violating_characters