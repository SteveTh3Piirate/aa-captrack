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

    def render(self, request):
        """
        Hide menu item for users without permission.

        Works with older AllianceAuth versions where menu hooks are called
        with no args (hook()), because render() still receives request.
        """
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return ""

        if not user.has_perm("captrack.basic_access"):
            return ""

        return super().render(request)


@hooks.register("menu_item_hook")
def register_captrack_menu():
    # NOTE: Older AA versions call menu_item_hook with no args.
    return CapTrackMenu()
