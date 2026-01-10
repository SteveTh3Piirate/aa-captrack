from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from .models import CapTrackSettings
from .services import get_capitals_in_blacklisted_regions
from .models import CapAlertCooldown


COOLDOWN_MINUTES = 30


@shared_task
def scan_capitals_and_send_alerts():
    try:
        settings = CapTrackSettings.objects.first()
        if not settings or not settings.webhook_url:
            return
    except CapTrackSettings.DoesNotExist:
        return

    blacklisted = settings.blacklisted_regions.all()
    entries = get_capitals_in_blacklisted_regions(blacklisted)

    now = timezone.now()

    for entry in entries:
        ownership = entry["ownership"]
        char = ownership.character
        char_id = char.character_id

        # Check cooldown
        cooldown, _ = CapAlertCooldown.objects.get_or_create(
            character_id=char_id,
            defaults={"last_alert": now - timedelta(hours=1)}
        )

        if cooldown.last_alert > now - timedelta(minutes=COOLDOWN_MINUTES):
            continue  # still cooling down

        # Build webhook message
        payload = {
            "content": (
                f"⚠️ **Capital detected in blacklisted region!**\n"
                f"**Pilot:** {char.character_name}\n"
                f"**Ship:** {entry['ship_type']}\n"
                f"**System:** {entry['system']}\n"
                f"**Structure:** {entry['structure']}"
            )
        }

        # Send webhook
        import requests
        requests.post(settings.webhook_url, json=payload)

        # Update cooldown
        cooldown.last_alert = now
        cooldown.save()
