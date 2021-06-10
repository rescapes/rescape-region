import reversion
from django.contrib.auth import get_user_model
from django.contrib.gis.db.models import SET_NULL, CASCADE, Q
from django.db.models import (
    CharField,
    ForeignKey, ManyToManyField, UniqueConstraint)
from django.db.models import JSONField
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import feature_collection_default, project_data_default
from rescape_region.models.revision_mixin import RevisionModelMixin


@reversion.register()
class Project(SafeDeleteModel, RevisionModelMixin):
    """
        Models a geospatial project
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=50, null=False)
    name = CharField(max_length=50, null=False)
    # TODO probably unneeded. Locations have geojson
    geojson = JSONField(null=False, default=feature_collection_default)
    data = JSONField(null=False, default=project_data_default)
    # The optional Region of the Project.
    # Don't create a related name. It leads Graphene to register classes by following the reverse relationship.
    # We don't want this because we might use Region but have our own Project class. This prevents Graphene from
    # reaching Project from Region
    region = ForeignKey('Region', null=True, on_delete=SET_NULL, related_name='+', )
    # Locations in the project. It might be better in some cases to leave this empty and specify locations by queries
    locations = ManyToManyField('Location', blank=True, related_name='projects')

    # Projects must be owned by someone
    user = ForeignKey(get_user_model(), on_delete=CASCADE, related_name='+', )

    class Meta:
        app_label = "rescape_region"
        constraints = [
            # https://stackoverflow.com/questions/33307892/django-unique-together-with-nullable-foreignkey
            # This says that for deleted locations, user and key and deleted date must be unique
            UniqueConstraint(fields=['user', 'deleted', 'key'],
                             name='unique_project_with_deleted'),
            # This says that for non-deleted locations, user and key must be unique
            UniqueConstraint(fields=['user', 'key'],
                             condition=Q(deleted=None),
                             name='unique_project_without_deleted'),
        ]

    def __str__(self):
        return self.name
