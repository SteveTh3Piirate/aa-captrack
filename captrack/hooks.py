# captrack/hooks.py

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook
from django.utils.translation import gettext_lazy as _

from .constants import CAPTRACK_BASIC_ACCESS_PERM

# IMPORTANT:
# Import the app's urls module so UrlHook has access to urlpatterns
from . import urls as captrack_urls


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
        Compatible with older AllianceAuth versions.
        """
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return ""

        if not user.has_perm(CAPTRACK_BASIC_ACCESS_PERM):
            return ""

        return super().render(request)


@hooks.register("menu_item_hook")
def register_captrack_menu():
    return CapTrackMenu()


@hooks.register("url_hook")
def register_urls():
    """
    Expose /captrack/ automatically without modifying myauth/urls.py
    """
    return UrlHook(captrack_urls, "captrack", r"^captrack/")
