from django.contrib.gis.db.models import GeometryField
from django.db.models import (
    CharField, Model,
    DateTimeField)


def default():
    return dict()


def default_geometry():
    """
    The default geometry is a polygon of the earth's extent
    :return:
    """
    from rescape_graphene import ewkt_from_feature
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

    name = CharField(max_length=50, null=True)
    description = CharField(max_length=500, unique=False, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    geometry = GeometryField(null=False, default=lambda: default_geometry())

    class Meta:
        app_label = "app"

    def __str__(self):
        return self.name
