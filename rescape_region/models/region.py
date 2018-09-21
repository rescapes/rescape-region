from django.db import models
from django.db.models import (
    CharField,
    DateTimeField, ForeignKey)
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db.models import Model

from rescape_region.model_helpers import region_default


class Region(Model):
    """
        Models a geospatial region
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=20, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    # Boundary of the Region. This is required by can be initialized to default_feature_collection_geometry()
    # which is the extend of earth if no restrictions are needed. Boundary is intended for setting the viewport
    # of a map, although it could also outline the region or something else
    boundary = ForeignKey('FeatureCollection', related_name='regions', null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=region_default)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name
