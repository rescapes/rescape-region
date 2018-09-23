from django.contrib.gis.db.models import GeometryCollectionField, GeometryField, Model
from django.db.models import (
    CharField,
    DateTimeField)

from rescape_region.model_helpers import feature_geometry_default


class Feature(Model):
    """
        Models a geospatial feature along with some metadata. The metadata like name and description
        could be populated by the geojson that populates the geometry column
        (using for instance rescape_python_helpers.geometry_from_geojson).
        The reason we make a separate model for Feature rather than having classes like Region just use a
        GeometryField or GeometryCollectionField directly has to do with the implementation supporting
        geospatial fields in graphene, which can't handle multiple geospatial fields but can handle multiple
        foreign keys that point to objects one geospatial field.
    """

    # Optional name of a feature.
    name = CharField(max_length=50, null=True)
    # Optional description of a feature. This might be supplanted by the description in the geometry's geojson
    description = CharField(max_length=500, unique=False, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    geo = GeometryField(null=False, default=feature_geometry_default)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name

