import sys
import importlib.util
from django.apps import AppConfig


class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "captrack"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        In production (AllianceAuth), load hooks/tasks.
        In dev/test environments where AllianceAuth or CorpTools may not be installed,
        skip these imports so makemigrations/migrate can run.
        """
        # Skip during migration-ish commands
        skip_cmds = {"makemigrations", "migrate", "showmigrations", "check", "collectstatic"}
        if any(cmd in sys.argv for cmd in skip_cmds):
            return

        # If AllianceAuth isn't installed, don't import hooks/tasks
        if importlib.util.find_spec("allianceauth") is None:
            return

        # Now safe to import
        import captrack.hooks  # noqa
        import captrack.tasks  # noqa
