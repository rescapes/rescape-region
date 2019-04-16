from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import OneToOneField, CharField
from django.contrib.gis.db.models import Model

from rescape_region.model_helpers import user_state_data_default


class Settings(Model):
    """
        Global settings. This is a single instance class at the moment but can be expanded to handle different
        servers and other global settings that need to be customized by geographic region or similar.
        No user settings are stored here, that is all stored in UserState
    """
    # Unique human readable identifier
    key = CharField(max_length=20, unique=True, null=False)
    data = JSONField(null=False, default=user_state_data_default)

    class Meta:
        app_label = "rescape_region"
