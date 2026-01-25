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
        help_text="Select regions to blacklist for capital tracking."
    )

    webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text="Discord webhook URL for cap notifications."
    )

    # Optional Discord mentions (IDs) to ping when an alert is posted.
    # Stored as comma-separated numeric IDs to keep admin UX simple.
    discord_mention_roles = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text=(
            "Optional: comma-separated Discord Role IDs to ping on alerts. "
            "Example: 123456789012345678,234567890123456789"
        ),
    )
    discord_mention_users = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text=(
            "Optional: comma-separated Discord User IDs to ping on alerts. "
            "Example: 123456789012345678"
        ),
    )

    class Meta:
        verbose_name = "CapTrack"
        verbose_name_plural = "CapTrack Dashboard"
        permissions = (
            ("basic_access", "Can View Dashboard"),
        )

    def __str__(self):
        return "CapTrack Settings"

    def send_test_webhook(self):
        """
        Sends a simple test message to the configured Discord webhook.
        """
        if not self.webhook_url:
            raise ValidationError("Webhook URL is not set.")

        from .utils.discord import build_discord_mentions

        mention_text, allowed_mentions = build_discord_mentions(
            roles_csv=self.discord_mention_roles,
            users_csv=self.discord_mention_users,
        )

        payload = {
            "content": (mention_text + " " if mention_text else "") + "CapTrack test webhook successful.",
            "allowed_mentions": allowed_mentions,
        }
        response = requests.post(self.webhook_url, json=payload, timeout=5)

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
        help_text="Character currently being monitored for capital movement."
    )

    first_detected = models.DateTimeField(
        auto_now_add=True,
        help_text="When this character was first detected with a capital in a blacklisted region."
    )

    # Controlled by refresh logic (services/tasks), not auto-updated by model saves
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this character was last confirmed with a capital in a blacklisted region."
    )

    # When we last sent an alert for this watch entry
    last_alert_sent = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When an alert was last sent for this watchlist entry."
    )

    # Allow ops to snooze alerts until a certain time
    alert_snoozed_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="If set, alerts are suppressed until this time."
    )

    class Meta:
        verbose_name = "CapTrack watchlist entry"
        verbose_name_plural = "CapTrack watchlist"

    def __str__(self):
        name = getattr(getattr(self.character, "character", None), "character_name", self.character.pk)
        return f"Watchlist: {name}"
