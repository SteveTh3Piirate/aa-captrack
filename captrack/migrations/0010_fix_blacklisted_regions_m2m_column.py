from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("captrack", "0009_merge_20260318_1314"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE captrack_captracksettings_blacklisted_regions
                RENAME COLUMN everegion_id TO region_id;
            """,
            reverse_sql="""
                ALTER TABLE captrack_captracksettings_blacklisted_regions
                RENAME COLUMN region_id TO everegion_id;
            """,
        )
    ]
