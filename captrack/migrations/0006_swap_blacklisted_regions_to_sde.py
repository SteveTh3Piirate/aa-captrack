from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eve_sde", "0001_initial"),
        ("captrack", "0005_capwatchlist_alert_snoozed_until_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="captracksettings",
            name="blacklisted_regions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Select regions to blacklist for capital tracking.",
                related_name="captrack_blacklisted_regions",
                to="eve_sde.region",
            ),
        ),
    ]
