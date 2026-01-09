from django.db import models
from eveuniverse.models import EveRegion


class CapTrackSettings(models.Model):
    """
    Stores the blacklist of region names.
    CapTrack uses this to filter corp member capitals
    based on their last known location from Corptools.
    """

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