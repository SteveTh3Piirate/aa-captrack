from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook
from django.utils.translation import gettext_lazy as _


class CapTrackMenu(MenuItemHook):
    def __init__(self):
        super().__init__(
            _("CapTrack"),
            "fas fa-satellite-dish",
            "captrack:dashboard",
            navactive=["captrack:"],
            order=200,
        )


@hooks.register("menu_item_hook")
def register_captrack_menu(request):
    """
    Only show menu item to users with captrack.basic_access.
    Older AA versions don't support `permissions=` in MenuItemHook.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    if not user.has_perm("captrack.basic_access"):
        return None

    return CapTrackMenu()
