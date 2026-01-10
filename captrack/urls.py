from django.apps import AppConfig
from allianceauth.services.hooks import register_hookset
from .hooks import CapTrackHookSet

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "aa_captrack"

    def ready(self):
        register_hookset(CapTrackHookSet())
