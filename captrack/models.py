from django.db import models
from eveuniverse.models import EveRegion


class CapTrackSettings(models.Model):
    id = models.BigAutoField(primary_key=True)

    blacklisted_regions = models.ManyToManyField(
        EveRegion,
        blank=True,
        help_text="Select regions to blacklist for capital tracking."
    )

    class Meta:
        verbose_name = "CapTrack settings"
        verbose_name_plural = "CapTrack settings"

    def __str__(self):
        return "CapTrack Settings"