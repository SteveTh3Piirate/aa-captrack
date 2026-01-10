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

    # EveUniverse regions use .id (ESI region ID)
    region_ids = [r.id for r in blacklisted_regions]

    # Pull all capital ship assets with full location + type resolution
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

    # Corptools MapRegion uses .region_id (also ESI region ID)
    assets = [
        a for a in assets
        if a.location_name
        and a.location_name.system
        and a.location_name.system.constellation.region.region_id in region_ids
    ]

    violating_characters = []

    for asset in assets:
        # Extract the ESI character ID from Corptools
        char_id = asset.character.character.character_id

        try:
            # Convert to a real AllianceAuth EveCharacter model instance
            char_obj = EveCharacter.objects.get(character_id=char_id)
            violating_characters.append(char_obj)
        except EveCharacter.DoesNotExist:
            # Skip characters not linked in AA
            continue

    return violating_characters