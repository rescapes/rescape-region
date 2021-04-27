import reversion
from django.db.models import (
    CharField, UniqueConstraint, Q)
from django.db.models import JSONField
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import region_data_default, feature_collection_default
from rescape_region.models.revision_mixin import RevisionModelMixin

def default_search_identification():
    return dict()

def default_search_street():
    return dict()

@reversion.register()
class SearchLocation(SafeDeleteModel, RevisionModelMixin):
    """
        Models a location search that can match zero to many locations
    """

    # Search for matches with the id and key (location.id, location.key)
    identification = JSONField(default=default_search_identification)

    # Search for matches with the street name (location.name)
    street = JSONField(default=default_search_street)

    # Search for matches with the location.geojson fields
    geojson = JSONField(null=False, default=feature_collection_default)
    # Search for matches with the location.data fields
    data = JSONField(null=False, default=region_data_default)

    class Meta:
        app_label = "rescape_region"
