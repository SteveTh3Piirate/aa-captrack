from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .models import CapTrackSettings
from .services import (
    get_capitals_in_blacklisted_regions,
    group_capitals_by_main,
)


@login_required
@permission_required("captrack.basic_access", raise_exception=True)
def dashboard(request):
    settings = CapTrackSettings.objects.first()
    blacklisted_regions = settings.blacklisted_regions.all() if settings else []

    raw_entries = get_capitals_in_blacklisted_regions(blacklisted_regions)
    groups = group_capitals_by_main(raw_entries)

    return render(
        request,
        "captrack/dashboard.html",
        {
            "blacklisted_regions": blacklisted_regions,
            "groups": groups,
        }
    )
