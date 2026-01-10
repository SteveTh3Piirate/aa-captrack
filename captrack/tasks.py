from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from .models import (
    CapTrackSettings,
    CapAlertCooldown,
    CapWatchlist,
)
from .services import get_capitals_in_blacklisted_regions


COOLDOWN_MINUTES = 360  # minutes


# ------------------------------------------------------------
#  MAIN 5-MINUTE SCANNER
# ------------------------------------------------------------
@shared_task
def scan_capitals_and_send_alerts():
    """
    Main scheduled task:
    - Scans for capitals in blacklisted regions
    - Sends Discord alerts (with cooldown)
    - Maintains the CapWatchlist (add/remove characters)
    """
    try:
        settings = CapTrackSettings.objects.first()
        if not settings or not settings.webhook_url:
            return
    except CapTrackSettings.DoesNotExist:
        return

    blacklisted = settings.blacklisted_regions.all()
    entries = get_capitals_in_blacklisted_regions(blacklisted)

    now = timezone.now()

    # Track which characters are currently detected
    detected_ids = set()

    for entry in entries:
        ownership = entry["ownership"]
        char = ownership.character
        char_id = char.character_id
        detected_ids.add(char_id)

        # -----------------------------
        # Maintain WATCHLIST (add/update)
        # -----------------------------
        CapWatchlist.objects.get_or_create(character=ownership)

        # -----------------------------
        # Cooldown check
        # -----------------------------
        cooldown, _ = CapAlertCooldown.objects.get_or_create(
            character_id=char_id,
            defaults={"last_alert": now - timedelta(hours=1)}
        )

        if cooldown.last_alert > now - timedelta(minutes=COOLDOWN_MINUTES):
            continue  # still cooling down

        # -----------------------------
        # Build webhook message
        # -----------------------------
        payload = {
            "content": (
                f"⚠️ **Capital detected in blacklisted region!**\n"
                f"**Pilot:** {char.character_name}\n"
                f"**Ship:** {entry['ship_type']}\n"
                f"**System:** {entry['system']}\n"
                f"**Structure:** {entry['structure']}"
            )
        }

        # -----------------------------
        # Send webhook
        # -----------------------------
        import requests
        requests.post(settings.webhook_url, json=payload)

        # -----------------------------
        # Update cooldown
        # -----------------------------
        cooldown.last_alert = now
        cooldown.save()

    # ------------------------------------------------------------
    # CLEANUP WATCHLIST: remove characters no longer detected
    # ------------------------------------------------------------
    CapWatchlist.objects.exclude(
        character__character__character_id__in=detected_ids
    ).delete()


# ------------------------------------------------------------
#  6-HOUR TARGETED ASSET REFRESH
# ------------------------------------------------------------
@shared_task
def refresh_watchlist_assets():
    """
    Every 6 hours:
    - Refresh assets ONLY for characters in the watchlist
    - Uses CorpTools' update_subset_of_characters
    """
    from corptools.tasks import update_subset_of_characters

    watchlist = CapWatchlist.objects.all()

    char_ids = [
        entry.character.character.character_id
        for entry in watchlist
    ]

    if char_ids:
        update_subset_of_characters.apply_async(
            kwargs={"character_ids": char_ids}
        )
