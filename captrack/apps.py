from django.apps import AppConfig
from allianceauth.services.hooks import UrlHook
from django.urls import include, path

class CapTrackConfig(AppConfig):
    name = "captrack"
    label = "captrack"
    verbose_name = "CapTrack"

    def ready(self):
        UrlHook(
            urlconf_module="captrack.urls",
            namespace="captrack",
            url_pattern="captrack/"
        )