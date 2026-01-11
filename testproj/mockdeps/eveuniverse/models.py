from django.db import models


class EveRegion(models.Model):
    # Minimal fields needed for CapTrack relations/admin
    # (Real eveuniverse has region_id; keeping it is helpful for realism)
    region_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class EveConstellation(models.Model):
    constellation_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class EveSolarSystem(models.Model):
    solar_system_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class EveType(models.Model):
    type_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
