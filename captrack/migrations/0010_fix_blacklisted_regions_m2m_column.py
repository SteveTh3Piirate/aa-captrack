from django.db import migrations


TABLE_NAME = "captrack_captracksettings_blacklisted_regions"


def _column_names(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        desc = schema_editor.connection.introspection.get_table_description(cursor, TABLE_NAME)
    return {c.name for c in desc}


def forwards(apps, schema_editor):
    cols = _column_names(schema_editor)

    # If the legacy join column exists, rename it to match eve_sde.Region M2M naming.
    if "everegion_id" in cols and "region_id" not in cols:
        schema_editor.execute(
            f"ALTER TABLE {TABLE_NAME} RENAME COLUMN everegion_id TO region_id;"
        )


def backwards(apps, schema_editor):
    cols = _column_names(schema_editor)

    # Reverse the rename if applicable.
    if "region_id" in cols and "everegion_id" not in cols:
        schema_editor.execute(
            f"ALTER TABLE {TABLE_NAME} RENAME COLUMN region_id TO everegion_id;"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("captrack", "0009_merge_20260318_1314"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
