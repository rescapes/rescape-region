import reversion
from django.contrib.auth.models import Group
from django.db.models import JSONField
from django.db import models
from django.db.models import OneToOneField
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import group_state_data_default
from rescape_region.models.revision_mixin import RevisionModelMixin


@reversion.register()
class GroupState(SafeDeleteModel, RevisionModelMixin):
    """
        Group state reference a single Group.
        The json structure of data should be identical to that of UserState, but maybe in the future will
        have additional attributes that deal with groups
    """
    group = OneToOneField(Group, null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=group_state_data_default)

    class Meta:
        app_label = "rescape_region"
