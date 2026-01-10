from django.shortcuts import render
from .models import CapTrackSettings
from .services import get_capitals_in_blacklisted_regions

def dashboard(request):
    settings = CapTrackSettings.objects.first()
    blacklisted_regions = settings.blacklisted_regions.all() if settings else []

    groups = get_capitals_in_blacklisted_regions()

    return render(
        request,
        "captrack/dashboard.html",
        {
            "blacklisted_regions": blacklisted_regions,
            "groups": groups,
        }
    )
