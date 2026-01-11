import sys
from django.apps import AppConfig


class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "captrack"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Always register hooks (sidebar/menu)
        import captrack.hooks  # noqa

        # Avoid importing tasks (and thus corptools) during migration-related commands
        skip_cmds = {"makemigrations", "migrate", "showmigrations", "check", "collectstatic"}
        if any(cmd in sys.argv for cmd in skip_cmds):
            return

        import captrack.tasks  # noqa
