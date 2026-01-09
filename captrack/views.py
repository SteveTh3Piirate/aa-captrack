from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .models import CapTrackSettings
from .services import get_capitals_in_blacklisted_regions


@login_required
@permission_required("captrack.view_captracksettings", raise_exception=True)
def dashboard(request):
    # Load the single settings row
    settings_obj = CapTrackSettings.objects.first()

    if settings_obj:
        blacklisted_regions = list(settings_obj.blacklisted_regions.all())
    else:
        blacklisted_regions = []

    # Real Corptools-powered capital discovery
    regions_with_capitals = get_capitals_in_blacklisted_regions(blacklisted_regions)

    context = {
        "blacklisted_regions": blacklisted_regions,
        "regions_with_capitals": regions_with_capitals,
    }

    return render(request, "captrack/dashboard.html", context)