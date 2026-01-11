from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CapTrackSettings(models.Model):
    """
    Singleton configuration for CapTrack.

    Use CapTrackSettings.objects.get_or_create(pk=1, defaults=...) to ensure a single row.
    """

    # General
    is_enabled = models.BooleanField(default=True)

    # Tracking / group IDs
    tracked_group_ids = models.JSONField(default=list, blank=True)
    tracked_industrial_group_ids = models.JSONField(default=list, blank=True)

    # Classification labels
    class_display_names = models.JSONField(default=dict, blank=True)

    # Alert rules
    always_alert_classes = models.JSONField(default=list, blank=True)
    thresholds_by_class = models.JSONField(default=dict, blank=True)
    threshold_scope = models.CharField(
        max_length=32,
        default="same_main",
        choices=[
            ("same_main", "Same main"),
        ],
    )
    ignore_classes = models.JSONField(default=list, blank=True)

    include_tracked_only_in_dashboard = models.BooleanField(default=True)
    alerting_only_discord = models.BooleanField(default=True)

    # Discord integration
    discord_enabled = models.BooleanField(default=True)
    discord_webhook_url_critical = models.TextField(blank=True, default="")
    discord_webhook_url_alerts = models.TextField(blank=True, default="")

    discord_ping_policy = models.CharField(
        max_length=32,
        default="critical_only",
        choices=[
            ("none", "No pings"),
            ("critical_only", "Ping only on critical"),
            ("all_alerts", "Ping on all alerts"),
        ],
    )
    discord_ping_role_id = models.CharField(max_length=64, blank=True, default="")

    discord_message_mode = models.CharField(
        max_length=32,
        default="detailed",
        choices=[
            ("compact", "Compact"),
            ("detailed", "Detailed"),
        ],
    )
    discord_include_system_region = models.BooleanField(default=True)
    discord_include_dashboard_link = models.BooleanField(default=True)
    dashboard_base_url = models.TextField(blank=True, default="")

    # Snooze
    snooze_scope = models.CharField(
        max_length=32,
        default="per_pilot",
        choices=[
            ("per_pilot", "Per pilot"),
        ],
    )
    snooze_durations_minutes = models.JSONField(default=list, blank=True)

    # Dashboard UX
    dashboard_refresh_seconds = models.PositiveIntegerField(default=60)
    dashboard_default_collapsed = models.BooleanField(default=False)
    dashboard_remember_collapse_state = models.BooleanField(default=True)
    show_unclassified_bucket = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CapTrack Settings"
        verbose_name_plural = "CapTrack Settings"

    def __str__(self):
        return "CapTrack Settings"

    def clean(self):
        """
        Populate defaults on first save for missing / empty fields.
        """
        if not self.class_display_names:
            self.class_display_names = {
                "titan": "Titan",
                "supercarrier": "Supercarrier",
                "dread": "Dreadnought",
                "lancer_dread": "Lancer Dreadnought",
                "carrier": "Carrier",
                "fax": "Force Auxiliary",
                "industrial": "Capital Industrial",
                "unclassified": "Unclassified",
            }

        if not self.always_alert_classes:
            self.always_alert_classes = ["titan", "supercarrier"]

        if not self.thresholds_by_class:
            self.thresholds_by_class = {
                "dread": 5,
                "lancer_dread": 5,
                "carrier": 5,
                "fax": 5,
            }

        if not self.snooze_durations_minutes:
            self.snooze_durations_minutes = [60, 360, 1440]

    def save(self, *args, **kwargs):
        old = None
        if self.pk:
            try:
                old = CapTrackSettings.objects.get(pk=self.pk)
            except CapTrackSettings.DoesNotExist:
                old = None

        super().save(*args, **kwargs)

        # Write audit diff if we had an old copy
        if old:
            diff = {}
            tracked_fields = [
                "is_enabled",
                "tracked_group_ids",
                "tracked_industrial_group_ids",
                "class_display_names",
                "always_alert_classes",
                "thresholds_by_class",
                "threshold_scope",
                "ignore_classes",
                "include_tracked_only_in_dashboard",
                "alerting_only_discord",
                "discord_enabled",
                "discord_webhook_url_critical",
                "discord_webhook_url_alerts",
                "discord_ping_policy",
                "discord_ping_role_id",
                "discord_message_mode",
                "discord_include_system_region",
                "discord_include_dashboard_link",
                "dashboard_base_url",
                "snooze_scope",
                "snooze_durations_minutes",
                "dashboard_refresh_seconds",
                "dashboard_default_collapsed",
                "dashboard_remember_collapse_state",
                "show_unclassified_bucket",
            ]
            for field in tracked_fields:
                before = getattr(old, field)
                after = getattr(self, field)
                if before != after:
                    diff[field] = {"old": before, "new": after}

            if diff:
                CapTrackSettingsAudit.objects.create(settings=self, diff=diff)


class CapTrackSettingsAudit(models.Model):
    settings = models.ForeignKey(
        CapTrackSettings,
        on_delete=models.CASCADE,
        related_name="audit_entries",
    )
    changed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    changed_at = models.DateTimeField(default=timezone.now)
    diff = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "CapTrack Settings Audit"
        verbose_name_plural = "CapTrack Settings Audit"
        ordering = ("-changed_at",)

    def __str__(self):
        return f"CapTrackSettingsAudit {self.changed_at}"
