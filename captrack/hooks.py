from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook
from django.utils.translation import gettext_lazy as _

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