from django.db.models import (
    CharField,
    DateTimeField, ForeignKey, ManyToManyField)
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db.models import SET_NULL
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import feature_collection_default, project_data_default


class Project(SafeDeleteModel):
    """
        Models a geospatial project
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=20, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    # TODO probably unneeded. Locations have geojson
    geojson = JSONField(null=False, default=feature_collection_default)
    data = JSONField(null=False, default=project_data_default)
    # The optional Region of the Project.
    # Don't create a related name. It leads Graphene to register classes by following the reverse relationship.
    # We don't want this because we might use Region but have our own Project class. This prevents Graphene from
    # reaching Project from Region
    region = ForeignKey('Region', null=True, on_delete=SET_NULL, related_name='+',)
    # Locations in the project. It might be better in some cases to leave this empty and specify locations by queries
    locations = ManyToManyField('Location', blank=True)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name
