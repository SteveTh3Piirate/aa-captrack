from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from .models import CapTrackSettings
from eveuniverse.models import EveRegion


@admin.register(CapTrackSettings)
class CapTrackSettingsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("blacklisted_regions",)
    fields = ("blacklisted_regions", "webhook_url", "test_webhook_button")
    readonly_fields = ("test_webhook_button",)

    def has_add_permission(self, request):
        # Only allow one settings row
        return not CapTrackSettings.objects.exists()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "blacklisted_regions":
            kwargs["queryset"] = (
                EveRegion.objects.all()
                .exclude(name__regex=r"^[A-Z]-R\d{5}$")
                .exclude(name__regex=r"^[A-Z]{1,2}-\d{2}$")
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # -----------------------------
    # Test Webhook Button
    # -----------------------------
    def test_webhook_button(self, obj):
        if not obj.pk:
            return "Save settings first."
        return mark_safe(
            '<a class="button" '
            'style="padding:6px 10px; background:#5e9ed6; color:white; '
            'border-radius:4px; text-decoration:none;" '
            'href="test-webhook/">Send Test Webhook</a>'
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

        try:
            obj.send_test_webhook()  # your existing method
            self.message_user(request, "Webhook sent successfully.", messages.SUCCESS)
        except ValidationError as e:
            self.message_user(request, f"Webhook failed: {e}", messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Unexpected error: {e}", messages.ERROR)

        return redirect("../../")
