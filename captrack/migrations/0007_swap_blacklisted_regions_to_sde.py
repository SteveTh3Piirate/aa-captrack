from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eve_sde", "0014_dogmaeffect_description_de_and_more"),
        ("captrack", "0006_captracksettings_discord_mentions"),
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
