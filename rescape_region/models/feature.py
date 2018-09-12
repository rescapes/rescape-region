from django.contrib.gis.db.models import GeometryField
from django.db.models import (
    CharField, Model,
    DateTimeField)
from rescape_python_helpers import ewkt_from_feature


def default():
    return dict()


def default_geometry():
    """
    The default geometry is a polygon of the earth's extent
    :return:
    """
    return ewkt_from_feature(
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon", "coordinates": [[[-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180]]]
            }
        }
    )

class Feature(Model):
    """
        Models a geospatial feature. Location is the geometry with a type and coordinates. All other properties
        become properties when represented in graphql or as geojson. Feature is a foreign key to classes like
        Resource.
    """

    # Optional name of a feature.
    name = CharField(max_length=50, null=True)
    # Optional description of a feature. This might be supplanted by the description in the geometry's geojson
    description = CharField(max_length=500, unique=False, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    geometry = GeometryField(null=False, default=default_geometry)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name
