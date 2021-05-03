import reversion
from django.db.models import (
    CharField)
from django.db.models import JSONField
from rescape_region.models.revision_mixin import RevisionModelMixin
from safedelete.models import SafeDeleteModel


def default_jurisdiction_data():
    return dict()


@reversion.register()
class Jurisdiction(SafeDeleteModel, RevisionModelMixin):
    """
        A Jurisdiction
    """

    # Since we often have incomplete locations data, we keep list of intersecting street names
    # This prevents duplicating jurisdictions for a location lacking geojson
    # These should be ordered alphabetically and must be unique
    data = JSONField(null=False, default=default_jurisdiction_data)

    # Stores geojson from OSM that represents jurisdiction
    geojson = JSONField(null=True, blank=True)

    class Meta:
        app_label = "rescape_region"
