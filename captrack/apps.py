from django.apps import AppConfig
from allianceauth import hooks

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "captrack"

    def ready(self):
        # Import inside ready() so Django loads hooks at startup
        from . import hooks as captrack_hooks
        hooks.register_hook(captrack_hooks.register_captrack_menu)