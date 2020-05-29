from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import (
    CharField,
    DateTimeField, ForeignKey, ManyToManyField, BooleanField)
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db.models import SET_NULL, CASCADE
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import feature_collection_default, project_data_default, get_location_schema


class Project(SafeDeleteModel):
    """
        Models a geospatial project
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=50, unique=True, null=False)
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

    # Projects must be owned by someone
    user = ForeignKey(get_user_model(), on_delete=CASCADE, related_name='+',)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name
