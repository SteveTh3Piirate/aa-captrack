from django.contrib import admin
from .models import CapTrackSettings
from eveuniverse.models import EveRegion


@admin.register(CapTrackSettings)
class CapTrackSettingsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("blacklisted_regions",)
    fields = ("blacklisted_regions",)

    def has_add_permission(self, request):
        # Only allow one settings row
        return not CapTrackSettings.objects.exists()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "blacklisted_regions":
            kwargs["queryset"] = (
                EveRegion.objects.all()
                .exclude(name__regex=r"^[A-Z]-R\d{5}$")      # wormhole pseudo-regions
                .exclude(name__regex=r"^[A-Z]{1,2}-\d{2}$")  # wormhole constellations like VR-01
            )

        return super().formfield_for_manytomany(db_field, request, **kwargs)
