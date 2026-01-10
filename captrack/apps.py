from django.apps import AppConfig

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "captrack"
    verbose_name = "CapTrack"

    def ready(self):
        # Import inside ready() to avoid AppRegistryNotReady
        from allianceauth.services.hooks import UrlHook

        UrlHook(
            "captrack.urls",   # module path
            "captrack",        # namespace
            "captrack/"        # URL prefix
        )