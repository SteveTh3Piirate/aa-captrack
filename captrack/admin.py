from django.contrib import admin
from .models import CapTrackSettings


@admin.register(CapTrackSettings)
class CapTrackSettingsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("blacklisted_regions",)
    fields = ("blacklisted_regions",)

    def has_add_permission(self, request):
        # Only allow one settings row
        return not CapTrackSettings.objects.exists()