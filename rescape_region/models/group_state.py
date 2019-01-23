from django.contrib.auth.models import Group
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import OneToOneField
from django.contrib.gis.db.models import Model
from rescape_region.model_helpers import group_state_data_default


class GroupState(Model):
    """
        Group state reference a single Group.
        The json structure of data should be identical to that of UserState, but maybe in the future will
        have additional attributes that deal with groups
    """
    group = OneToOneField(Group, null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=group_state_data_default)

    class Meta:
        app_label = "rescape_region"
