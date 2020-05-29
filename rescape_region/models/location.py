from django.contrib.postgres.fields import JSONField
from django.db.models import (
    CharField,
    DateTimeField)
from safedelete.models import SafeDeleteModel
from rescape_region.model_helpers import region_data_default, feature_collection_default

class Location(SafeDeleteModel):
    """
        Models a geospatial location
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=20, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    geojson = JSONField(null=False, default=feature_collection_default)
    data = JSONField(null=False, default=region_data_default)


    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name

