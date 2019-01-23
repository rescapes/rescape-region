from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import OneToOneField
from django.contrib.gis.db.models import Model

from rescape_region.model_helpers import user_state_data_default


class UserState(Model):
    """
        User state reference a single User.
        It is designed to be a json blob that matches frontend end representation of the model data as closely
        as possible. This makes it as easy as possible to merge the model data representation with the active
        users settings and to execute queries that limit the user's access to data
    """
    user = OneToOneField(User, null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=user_state_data_default)

    class Meta:
        app_label = "rescape_region"
