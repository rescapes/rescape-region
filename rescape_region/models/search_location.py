import reversion
from django.db.models import JSONField, ManyToManyField, CharField
from safedelete.models import SafeDeleteModel

from rescape_region.models import SearchJurisdiction
from rescape_region.models.revision_mixin import RevisionModelMixin


def default_search_identification():
    return dict()

def default_search_street():
    return dict()

def data_default():
    return dict()

def geojson_default():
    return dict()

@reversion.register()
class SearchLocation(SafeDeleteModel, RevisionModelMixin):
    """
        Models a location search that can match zero to many locations
    """

    # Optional name of the search.
    name = CharField(max_length=100, null=True)

    # Optional way to know what type of search it is, such as 'mapbox' to specify searches only done on the map
    category = CharField(max_length=100, null=True)

    # Search for matches with the id and key (location.id, location.key)
    identification = JSONField(null=True, default=default_search_identification)

    # Search for matches with the street name (location.name)
    street = JSONField(null=True, default=default_search_street)

    # The jurisdictions to search when looking for locations
    jurisdictions = ManyToManyField(SearchJurisdiction, related_name='rescape_region_jurisdictions')

    # Search for matches with True location.geojson fields
    geojson = JSONField(null=True, default=geojson_default)

    # Search for matches with the location.data fields
    data = JSONField(null=True, default=data_default)

    class Meta:
        app_label = "rescape_region"
