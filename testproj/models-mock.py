from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from eveuniverse.models import EveRegion
import requests


class CapTrackSettings(models.Model):
    """
    Stores configuration for CapTrack, including which regions
    are considered blacklisted for capital ship presence.
    """
    id = models.BigAutoField(primary_key=True)

    blacklisted_regions = models.ManyToManyField(
        EveRegion,
        blank=True,
        help_text="Select regions to blacklist for capital tracking.",
    )

    webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text="Discord webhook URL for cap notifications.",
    )

    class Meta:
        verbose_name = "CapTrack settings"
        verbose_name_plural = "CapTrack settings"

    def __str__(self):
        return "CapTrack Settings"

    def send_test_webhook(self):
        """
        Sends a simple test message to the configured Discord webhook.
        """
        if not self.webhook_url:
            raise ValidationError("Webhook URL is not set.")

        payload = {"content": "CapTrack test webhook successful."}
        response = requests.post(self.webhook_url, json=payload)

        if response.status_code >= 400:
            raise ValidationError(
                f"Discord returned HTTP {response.status_code}: {response.text}"
            )


class CapAlertCooldown(models.Model):
    """
    Tracks cooldowns for capital alerts so the same character
    does not trigger repeated notifications too frequently.
    """
    character_id = models.BigIntegerField(db_index=True)
    last_alert = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "CapTrack alert cooldown"
        verbose_name_plural = "CapTrack alert cooldowns"

    def __str__(self):
        return f"Cooldown for {self.character_id} at {self.last_alert}"


class CapWatchlist(models.Model):
    """
    Tracks characters who currently have a capital in a blacklisted region.
    Used to trigger periodic asset refreshes and targeted re-scans.
    """
    character = models.OneToOneField(
        "authentication.CharacterOwnership",
        on_delete=models.CASCADE,
        related_name="captrack_watch",
        help_text="Character currently being monitored for capital movement.",
    )

    first_detected = models.DateTimeField(
        auto_now_add=True,
        help_text="When this character was first detected with a capital in a blacklisted region.",
    )

    last_seen = models.DateTimeField(
        auto_now=True,
        help_text="When this character was last confirmed with a capital in a blacklisted region.",
    )

    class Meta:
        verbose_name = "CapTrack watchlist entry"
        verbose_name_plural = "CapTrack watchlist"

    def __str__(self):
        # In mockdeps, CharacterOwnership->Character exists, so this will still work.
        name = getattr(self.character.character, "character_name", self.character.pk)
        return f"Watchlist: {name}"
