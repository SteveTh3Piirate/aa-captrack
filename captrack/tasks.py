from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from .models import CapTrackSettings, CapAlertCooldown, CapWatchlist
from .services import get_capitals_in_blacklisted_regions
from .utils.discord import build_captrack_embed, send_discord_webhook


COOLDOWN_MINUTES = 360  # minutes


def _get_character_id_from_ownership(ownership) -> int | None:
    """
    Best-effort resolver for character_id across AA model shapes.
    """
    # Common: ownership.character.character_id
    ch = getattr(ownership, "character", None)
    if ch is not None:
        cid = getattr(ch, "character_id", None)
        if cid:
            return cid
        # Sometimes ownership.character is a wrapper with .character.character_id
        inner = getattr(ch, "character", None)
        if inner is not None:
            cid2 = getattr(inner, "character_id", None)
            if cid2:
                return cid2
    return None


def _get_character_name_from_ownership(ownership) -> str:
    ch = getattr(ownership, "character", None)
    if ch is not None:
        name = getattr(ch, "character_name", None)
        if name:
            return name
        inner = getattr(ch, "character", None)
        if inner is not None:
            name2 = getattr(inner, "character_name", None)
            if name2:
                return name2
    return str(ownership)


# ------------------------------------------------------------
#  MAIN SCANNER
# ------------------------------------------------------------
@shared_task
def scan_capitals_and_send_alerts():
    """
    Scheduled task:
    - Scans for capitals in blacklisted regions
    - Sends Discord alerts (with cooldown)
    - Maintains the CapWatchlist (add/remove characters)
    """
    settings = CapTrackSettings.objects.first()
    if not settings or not settings.webhook_url:
        return

    blacklisted = settings.blacklisted_regions.all()
    entries = get_capitals_in_blacklisted_regions(blacklisted)

    now = timezone.now()

    # Track which characters are currently detected
    detected_ids = set()

    for entry in entries:
        ownership = entry["ownership"]
        char_id = _get_character_id_from_ownership(ownership)
        char_name = _get_character_name_from_ownership(ownership)

        if not char_id:
            continue

        detected_ids.add(char_id)

        # Maintain watchlist
        CapWatchlist.objects.get_or_create(character=ownership)

        # Cooldown check
        cooldown, _ = CapAlertCooldown.objects.get_or_create(
            character_id=char_id,
            defaults={"last_alert": now - timedelta(hours=1)},
        )

        if cooldown.last_alert > now - timedelta(minutes=COOLDOWN_MINUTES):
            continue

        # Build a nice embed w/ portrait + ship render (if type_id present)
        embed = build_captrack_embed(
            character_id=char_id,
            character_name=char_name,
            ship_type_name=entry["ship_type"],
            ship_type_id=entry.get("ship_type_id"),
            system_name=entry.get("system"),
            structure_name=entry.get("structure"),
            status_line=f"Detected • cooldown {COOLDOWN_MINUTES}m",
        )

        # Send
        ok = send_discord_webhook(settings.webhook_url, embeds=[embed])

        if ok:
            cooldown.last_alert = now
            cooldown.save()

    # Cleanup watchlist: remove characters no longer detected
    # (We need a safe way to compare ids from ownership)
    to_remove = []
    for wl in CapWatchlist.objects.select_related("character").all():
        wl_char_id = _get_character_id_from_ownership(wl.character)
        if wl_char_id and wl_char_id not in detected_ids:
            to_remove.append(wl.pk)

    if to_remove:
        CapWatchlist.objects.filter(pk__in=to_remove).delete()


# ------------------------------------------------------------
#  TARGETED ASSET REFRESH
# ------------------------------------------------------------
@shared_task
def refresh_watchlist_assets():
    """
    Every 6 hours:
    - Refresh assets ONLY for characters in the watchlist
    - Uses CorpTools' update_subset_of_characters
    """
    from corptools.tasks import update_subset_of_characters

    watchlist = CapWatchlist.objects.select_related("character").all()

    char_ids = []
    for entry in watchlist:
        cid = _get_character_id_from_ownership(entry.character)
        if cid:
            char_ids.append(cid)

    if char_ids:
        update_subset_of_characters.apply_async(kwargs={"character_ids": char_ids})
