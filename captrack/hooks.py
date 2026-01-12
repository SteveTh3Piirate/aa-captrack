from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook
from django.utils.translation import gettext_lazy as _

from .constants import CAPTRACK_BASIC_ACCESS_PERM


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

        Compatible with older AA versions where menu hooks are called with no args,
        because render() still receives request.
        """
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return ""

        if not user.has_perm(CAPTRACK_BASIC_ACCESS_PERM):
            return ""

        return super().render(request)


@hooks.register("menu_item_hook")
def register_captrack_menu():
    # NOTE: Older AA versions call menu_item_hook with no args.
    return CapTrackMenu()

@hooks.register("url_hook")
def register_urls():
    # This makes your app available at /captrack/ without editing myauth/urls.py
    return UrlHook(urls, "captrack", r"^captrack/")
