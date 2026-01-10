from django.apps import AppConfig

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "aa_captrack"   # <-- MUST be unique
    verbose_name = "CapTrack"

    def ready(self):
        from allianceauth.services.hooks import UrlHook

        UrlHook(
            "captrack.urls",
            "captrack",
            "captrack/"
        )