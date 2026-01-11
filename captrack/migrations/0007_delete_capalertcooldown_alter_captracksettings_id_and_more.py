from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("captrack", "0006_captrack_admin_settings"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS captrack_capalertcooldown;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name="CapAlertCooldown"),
            ],
        ),

        # ... leave the rest of your existing 0007 operations EXACTLY as they are ...
    ]
