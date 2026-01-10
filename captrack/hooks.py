from allianceauth import hooks
from allianceauth.services.hooks import UrlHook

@hooks.register("url_hook")
def register_captrack_urls():
    return UrlHook(
        "captrack.urls",   # module path
        "captrack",        # namespace
        "captrack/"        # prefix
    )