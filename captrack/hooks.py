from allianceauth.hooks import HookSet

class CapTrackHookSet(HookSet):
    def urls_hook(self):
        return [
            ("captrack.urls", "captrack", "captrack/")
        ]