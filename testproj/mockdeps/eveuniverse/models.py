from django.db import models

class EveRegion(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "mock_eveuniverse"

class EveConstellation(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "mock_eveuniverse"

class EveSolarSystem(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "mock_eveuniverse"

class EveType(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "mock_eveuniverse"