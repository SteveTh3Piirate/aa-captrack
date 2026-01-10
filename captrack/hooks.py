from allianceauth import hooks
from allianceauth.services.hooks import HookSet, MenuItemHook
from django.utils.translation import gettext_lazy as _

class CapTrackHookSet(HookSet):
    def urls_hook(self):
        return [
            ("captrack.urls", "captrack", "captrack/")
        ]

class CapTrackMenu(MenuItemHook):
    def __init__(self):
        super().__init__(
            _("CapTrack"),
            "fa fa-ship",
            "captrack:dashboard",
            navactive=["captrack:"],
            order=200,
        )

@hooks.register("menu_item_hook")
def register_captrack_menu():
    return CapTrackMenu()
