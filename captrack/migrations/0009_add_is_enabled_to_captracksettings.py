from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Depends on your current leaf/merge migration
        ("captrack", "0008_merge_20260111_1948"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Make the DB change idempotent for MariaDB/MySQL
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE captrack_captracksettings "
                        "ADD COLUMN IF NOT EXISTS is_enabled TINYINT(1) NOT NULL DEFAULT 1"
                    ),
                    reverse_sql=(
                        "ALTER TABLE captrack_captracksettings "
                        "DROP COLUMN IF EXISTS is_enabled"
                    ),
                ),
            ],
            # Make Django's model state match
            state_operations=[
                migrations.AddField(
                    model_name="captracksettings",
                    name="is_enabled",
                    field=models.BooleanField(
                        default=True,
                        help_text="If disabled, CapTrack is effectively paused (no alert processing).",
                    ),
                ),
            ],
        ),
    ]
