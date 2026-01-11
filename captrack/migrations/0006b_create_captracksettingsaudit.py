from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("captrack", "0006_captrack_admin_settings"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
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
                        to=settings.AUTH_USER_MODEL,
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
    ]
