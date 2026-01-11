from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def create_default_settings(apps, schema_editor):
    CapTrackSettings = apps.get_model("captrack", "CapTrackSettings")
    CapTrackSettings.objects.get_or_create(
        pk=1,
        defaults={
            "is_enabled": True,
            "class_display_names": {
                "titan": "Titan",
                "supercarrier": "Supercarrier",
                "dread": "Dreadnought",
                "lancer_dread": "Lancer Dreadnought",
                "carrier": "Carrier",
                "fax": "Force Auxiliary",
                "industrial": "Capital Industrial",
                "unclassified": "Unclassified",
            },
            "always_alert_classes": ["titan", "supercarrier"],
            "thresholds_by_class": {
                "dread": 5,
                "lancer_dread": 5,
                "carrier": 5,
                "fax": 5,
            },
            "threshold_scope": "same_main",
            "ignore_classes": [],
            "include_tracked_only_in_dashboard": True,
            "alerting_only_discord": True,
            "discord_enabled": True,
            "discord_webhook_url_critical": "",
            "discord_webhook_url_alerts": "",
            "discord_ping_policy": "critical_only",
            "discord_ping_role_id": "",
            "discord_message_mode": "detailed",
            "discord_include_system_region": True,
            "discord_include_dashboard_link": True,
            "dashboard_base_url": "",
            "snooze_scope": "per_pilot",
            "snooze_durations_minutes": [60, 360, 1440],
            "dashboard_refresh_seconds": 60,
            "dashboard_default_collapsed": False,
            "dashboard_remember_collapse_state": True,
            "show_unclassified_bucket": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("captrack", "0005_capwatchlist_alert_snoozed_until_and_more"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CapTrackSettings",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_enabled", models.BooleanField(default=True)),
                ("tracked_group_ids", models.JSONField(blank=True, default=list)),
                ("tracked_industrial_group_ids", models.JSONField(blank=True, default=list)),
                ("class_display_names", models.JSONField(blank=True, default=dict)),
                ("always_alert_classes", models.JSONField(blank=True, default=list)),
                ("thresholds_by_class", models.JSONField(blank=True, default=dict)),
                (
                    "threshold_scope",
                    models.CharField(
                        choices=[("same_main", "Same main")],
                        default="same_main",
                        max_length=32,
                    ),
                ),
                ("ignore_classes", models.JSONField(blank=True, default=list)),
                ("include_tracked_only_in_dashboard", models.BooleanField(default=True)),
                ("alerting_only_discord", models.BooleanField(default=True)),
                ("discord_enabled", models.BooleanField(default=True)),
                ("discord_webhook_url_critical", models.TextField(blank=True, default="")),
                ("discord_webhook_url_alerts", models.TextField(blank=True, default="")),
                (
                    "discord_ping_policy",
                    models.CharField(
                        choices=[
                            ("none", "No pings"),
                            ("critical_only", "Ping only on critical"),
                            ("all_alerts", "Ping on all alerts"),
                        ],
                        default="critical_only",
                        max_length=32,
                    ),
                ),
                ("discord_ping_role_id", models.CharField(blank=True, default="", max_length=64)),
                (
                    "discord_message_mode",
                    models.CharField(
                        choices=[("compact", "Compact"), ("detailed", "Detailed")],
                        default="detailed",
                        max_length=32,
                    ),
                ),
                ("discord_include_system_region", models.BooleanField(default=True)),
                ("discord_include_dashboard_link", models.BooleanField(default=True)),
                ("dashboard_base_url", models.TextField(blank=True, default="")),
                (
                    "snooze_scope",
                    models.CharField(
                        choices=[("per_pilot", "Per pilot")],
                        default="per_pilot",
                        max_length=32,
                    ),
                ),
                ("snooze_durations_minutes", models.JSONField(blank=True, default=list)),
                ("dashboard_refresh_seconds", models.PositiveIntegerField(default=60)),
                ("dashboard_default_collapsed", models.BooleanField(default=False)),
                ("dashboard_remember_collapse_state", models.BooleanField(default=True)),
                ("show_unclassified_bucket", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "CapTrack Settings",
                "verbose_name_plural": "CapTrack Settings",
            },
        ),
        migrations.CreateModel(
            name="CapTrackSettingsAudit",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(default=timezone.now)),
                ("diff", models.JSONField(blank=True, default=dict)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="auth.user",
                    ),
                ),
                (
                    "settings",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_entries",
                        to="captrack.captracksettings",
                    ),
                ),
            ],
            options={
                "verbose_name": "CapTrack Settings Audit",
                "verbose_name_plural": "CapTrack Settings Audit",
                "ordering": ("-changed_at",),
            },
        ),
        migrations.RunPython(create_default_settings, migrations.RunPython.noop),
    ]
