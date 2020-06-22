import reversion
from django.contrib.postgres.fields import JSONField
from django.db.models import (
    CharField)
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import region_data_default, feature_collection_default
from rescape_region.models.revision_mixin import RevisionModelMixin


@reversion.register()
class Region(SafeDeleteModel, RevisionModelMixin):
    """
        Models a geospatial region
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=50, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    # Stores geojson from OSM that represents the Location.
    # Note that this isn't stored as a GEOS GeometryCollection because that structure doesn't include properties
    # and other meta data that we want to keep from Open Street Map. It should still be possible to do PostGIS
    # operations in the database if needed by extracting the geometry from the geojson and casting it
    geojson = JSONField(null=False, default=feature_collection_default)
    data = JSONField(null=False, default=region_data_default)


    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name

