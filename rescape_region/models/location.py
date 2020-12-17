import reversion
from django.db.models import (
    CharField, UniqueConstraint, Q)
from django.db.models import JSONField
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import region_data_default, feature_collection_default
from rescape_region.models.revision_mixin import RevisionModelMixin

@reversion.register()
class Location(SafeDeleteModel, RevisionModelMixin):
    """
        Models a geospatial location
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=50, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    geojson = JSONField(null=False, default=feature_collection_default)
    data = JSONField(null=False, default=region_data_default)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name
