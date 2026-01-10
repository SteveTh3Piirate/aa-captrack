from collections import defaultdict

from corptools.models.assets import CharacterAsset
from corptools.models.audits import CharacterAudit
from eveuniverse.models import EveRegion


CAPITAL_GROUP_IDS = [30, 485, 547, 659, 1538]


def get_capitals_in_blacklisted_regions(blacklisted_regions):
    """
    Returns a structure:
    [
        {
            "region": EveRegion,
            "capitals": [
                {
                    "character_name": str,
                    "ship_type": str,
                    "system_name": str,
                    "structure_name": str or None,
                }
            ]
        }
    ]
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
        and a.location_name.system.constellation.region.region_id in region_ids
    ]

    # Group by region
    grouped = defaultdict(list)

    for asset in assets:
        region = asset.location_name.system.constellation.region

        grouped[region].append({
            "character_name": asset.character.character.character_name,
            "ship_type": asset.type_name.name,
            "system_name": asset.location_name.system.name,
            "structure_name": asset.location_name.location_name,
        })

    # Convert to list format for template
    output = []
    for region, capitals in grouped.items():
        output.append({
            "region": region,
            "capitals": capitals,
        })

    return output