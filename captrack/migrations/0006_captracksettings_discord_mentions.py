from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("captrack", "0005_capwatchlist_alert_snoozed_until_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="captracksettings",
            name="discord_mention_roles",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Optional: comma-separated Discord Role IDs to ping on alerts. "
                    "Example: 123456789012345678,234567890123456789"
                ),
                max_length=512,
            ),
        ),
        migrations.AddField(
            model_name="captracksettings",
            name="discord_mention_users",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Optional: comma-separated Discord User IDs to ping on alerts. "
                    "Example: 123456789012345678"
                ),
                max_length=512,
            ),
        ),
    ]
