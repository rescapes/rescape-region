import reversion
from django.db.models import JSONField, ManyToManyField
from safedelete.models import SafeDeleteModel

from rescape_region.models.revision_mixin import RevisionModelMixin

def default_search_identification():
    return dict()

def default_search_jursidiction_data():
    return dict()

def default_geojson():
    return dict()

@reversion.register()
class SearchJurisdiction(SafeDeleteModel, RevisionModelMixin):
    """
        Models a location search that can match zero to many locations
    """

    # Search for matches with the id
    identification = JSONField(null=True, default=default_search_identification)

    # Search for matches with the location.data fields
    data = JSONField(null=True, default=default_search_jursidiction_data)

    # Search for matches with True location.geojson fields
    geojson = JSONField(null=True, default=default_geojson)

    class Meta:
        app_label = "rescape_region"
