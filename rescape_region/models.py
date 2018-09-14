from django.contrib.gis.db.models import GeometryField
from django.db.models import (
    CharField, Model,
    DateTimeField)
from rescape_python_helpers import ewkt_from_feature
from django.db.models import (
    CharField,  Model,
    DateTimeField)
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Model, ForeignKey, OneToOneField


def default():
    return dict()


def default_geometry():
    """
    The default geometry is a polygon of the earth's extent
    :return:
    """
    return ewkt_from_feature(
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon", "coordinates": [[[-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180]]]
            }
        }
    )

class Feature(Model):
    """
        Models a geospatial feature. Location is the geometry with a type and coordinates. All other properties
        become properties when represented in graphql or as geojson. Feature is a foreign key to classes like
        Resource.
    """

    # Optional name of a feature.
    name = CharField(max_length=50, null=True)
    # Optional description of a feature. This might be supplanted by the description in the geometry's geojson
    description = CharField(max_length=500, unique=False, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    geometry = GeometryField(null=False, default=default_geometry)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name


class Region(Model):
    """
        Models a geospatial region
    """

    # Unique human readable identifier for URLs, etc
    key = CharField(max_length=20, unique=True, null=False)
    name = CharField(max_length=50, null=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    boundary = ForeignKey(Feature, related_name='regions', null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=default)

    class Meta:
        app_label = "rescape_region"

    def __str__(self):
        return self.name


def user_state_default():
    return dict(resources=[])


def group_state_default():
    return dict(resources=[])


class UserState(Model):
    """
        User state reference a single User.
        It is designed to be a json blob that matches frontend end representation of the model data as closely
        as possible. This makes it as easy as possible to merge the model data representation with the active
        users settings and to execute queries that limit the user's access to data
    """
    user = OneToOneField(User, null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=user_state_default)

    class Meta:
        app_label = "rescape_region"


class GroupState(Model):
    """
        Group state reference a single Group.
        The json structure of data should be identical to that of UserState, but maybe in the future will
        have additional attributes that deal with groups
    """
    group = OneToOneField(User, null=False, on_delete=models.CASCADE)
    data = JSONField(null=False, default=user_state_default)

    class Meta:
        app_label = "rescape_region"
