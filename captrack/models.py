from django.db import models
from eveuniverse.models import EveRegion
from django.core.exceptions import ValidationError
from django.utils import timezone
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
        help_text="Select regions to blacklist for capital tracking."
    )

    webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text="Discord webhook URL for cap notifications."
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

        payload = {
            "content": "CapTrack test webhook successful."
        }

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

    def __str__(self):
        return f"Cooldown for {self.character_id} at {self.last_alert}"
