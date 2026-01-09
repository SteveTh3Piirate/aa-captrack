import logging
from django.utils import timezone
from django.db import transaction

from .models import HomeConfig, TrackedCapital, MovementAlert
from .helpers import get_capital_assets_for_corps

logger = logging.getLogger(__name__)


def calculate_distance_jumps(home_system_id: int, target_system_id: int) -> int:
    """Placeholder for jump distance calculation."""
    # TODO: integrate with eveuniverse or your own distance logic.
    # For now, just return 0 so the pipeline works.
    return 0


def scan_capitals_for_corps(corp_ids):
    """Main scan function to be wired into Celery later."""
    try:
        home_cfg = HomeConfig.objects.first()
        if not home_cfg:
            logger.warning("CapTrack: No HomeConfig defined, skipping scan.")
            return

        assets = get_capital_assets_for_corps(corp_ids)

        for asset in assets:
            # You’ll adjust these attributes to match CorpTools’ model fields.
            character_id = asset.character_id
            character_name = asset.character_name
            ship_type_id = asset.type_id
            ship_type_name = asset.type_name
            system_id = asset.location_system_id
            system_name = asset.location_system_name

            distance = calculate_distance_jumps(
                home_cfg.home_system_id, system_id
            )

            with transaction.atomic():
                tracked, created = TrackedCapital.objects.get_or_create(
                    character_id=character_id,
                    ship_type_id=ship_type_id,
                    defaults={
                        "character_name": character_name,
                        "ship_type_name": ship_type_name,
                        "system_id": system_id,
                        "system_name": system_name,
                        "distance_from_home": distance,
                    },
                )

                if not created:
                    old_system = tracked.system_name
                    old_distance = tracked.distance_from_home

                    tracked.character_name = character_name
                    tracked.ship_type_name = ship_type_name
                    tracked.system_id = system_id
                    tracked.system_name = system_name
                    tracked.distance_from_home = distance
                    tracked.last_seen = timezone.now()
                    tracked.save()

                    # Movement detection + alert condition
                    if (
                        old_system != system_name
                        and distance is not None
                        and distance > home_cfg.allowed_jumps
                    ):
                        MovementAlert.objects.create(
                            character_name=character_name,
                            ship_type_name=ship_type_name,
                            old_system=old_system or "Unknown",
                            new_system=system_name or "Unknown",
                            distance_from_home=distance,
                        )

    except Exception:
        logger.exception("CapTrack: Error during capital scan")