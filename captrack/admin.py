from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from .models import CapTrackSettings, CapWatchlist
from eveuniverse.models import EveRegion


# ------------------------------------------------------------
#  CapTrack Settings Admin
# ------------------------------------------------------------
@admin.register(CapTrackSettings)
class CapTrackSettingsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("blacklisted_regions",)
    fields = ("blacklisted_regions", "webhook_url", "test_webhook_button")
    readonly_fields = ("test_webhook_button",)

    def has_add_permission(self, request):
        # Only one settings object allowed
        return not CapTrackSettings.objects.exists()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "blacklisted_regions":
            kwargs["queryset"] = (
                EveRegion.objects.all()
                .exclude(name__regex=r"^[A-Z]-R\d{5}$")   # wormhole pseudo-regions
                .exclude(name__regex=r"^[A-Z]{1,2}-\d{2}$")  # wormhole constellations
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def test_webhook_button(self, obj):
        if not obj.pk:
            return "Save settings first."
        return mark_safe(
            f'<a class="button" '
            f'style="padding:6px 10px; background:#5e9ed6; color:white; '
            f'border-radius:4px; text-decoration:none;" '
            f'href="../../{obj.pk}/test-webhook/">Send Test Webhook</a>'
        )

    test_webhook_button.short_description = "Webhook Test"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/test-webhook/",
                self.admin_site.admin_view(self.test_webhook_view),
                name="captrack_test_webhook",
            )
        ]
        return custom + urls

    def test_webhook_view(self, request, object_id):
        obj = self.get_object(request, object_id)

        if obj is None:
            self.message_user(request, "Settings object not found.", messages.ERROR)
            return redirect("../../")

        try:
            obj.send_test_webhook()
            self.message_user(request, "Webhook sent successfully.", messages.SUCCESS)
        except ValidationError as e:
            self.message_user(request, f"Webhook failed: {e}", messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Unexpected error: {e}", messages.ERROR)

        return redirect("../../")


# ------------------------------------------------------------
#  CapWatchlist Admin
# ------------------------------------------------------------
@admin.register(CapWatchlist)
class CapWatchlistAdmin(admin.ModelAdmin):
    """
    Displays characters currently being monitored for capital movement.
    This list is maintained automatically by the scanner.
    """
    list_display = (
        "character_name",
        "character_id",
        "first_detected",
        "last_seen",
    )
    search_fields = (
        "character__character__character_name",
        "character__character__character_id",
    )
    readonly_fields = (
        "character",
        "first_detected",
        "last_seen",
    )

    def has_add_permission(self, request):
        # Watchlist entries are created automatically by the scanner
        return False

    def character_name(self, obj):
        return obj.character.character.character_name

    def character_id(self, obj):
        return obj.character.character.character_id

    character_name.short_description = "Character"
    character_id.short_description = "Character ID"
