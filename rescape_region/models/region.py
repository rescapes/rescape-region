from .feature import Feature
from django.contrib.gis.db import models
from django.contrib.gis.db.models import  ForeignKey
from django.db.models import (
    CharField,  Model,
    DateTimeField)
from django.contrib.postgres.fields import JSONField

def default():
    return dict()

class Region(Model):
    """
        Models a geospatial region
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=20, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    boundary = ForeignKey(Feature, related_name='regions', null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=default)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name
