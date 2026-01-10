from django.apps import AppConfig

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "captrack"
    verbose_name = "CapTrack"

    def ready(self):
        # Import inside ready() to avoid AppRegistryNotReady
        from allianceauth.services.hooks import UrlHook
        from django.urls import include, path

        UrlHook(
            urlconf_module="captrack.urls",
            namespace="captrack",
            url_pattern="captrack/"
        )