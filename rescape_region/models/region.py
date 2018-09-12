from django.contrib.auth import get_user_model

from .feature import Feature
from django.contrib.gis.db import models
from django.contrib.gis.db.models import  ForeignKey
from django.db.models import (
    CharField,  Model,
    DateTimeField)
from django.contrib.postgres.fields import JSONField
from rescape_python_helpers import ewkt_from_feature

def default():
    return dict()


def default_geometry():
    ewkt_from_feature(
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon", "coordinates": [[[-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180]]]
        }
    }
)

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
    owner = ForeignKey(get_user_model(), null=False, related_name='regions', on_delete=models.CASCADE)

    class Meta:
        app_label = "app"

    def __str__(self):
        return self.name
