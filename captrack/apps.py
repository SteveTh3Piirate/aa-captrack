from django.apps import AppConfig
from .hooks import CapTrackHookSet

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "aa_captrack"
    verbose_name = "CapTrack"

    def ready(self):
        from allianceauth.hooks import register_hookset
        register_hookset(CapTrackHookSet())