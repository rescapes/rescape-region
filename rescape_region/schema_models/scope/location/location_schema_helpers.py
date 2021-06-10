import graphene
from graphene import Field, List
from graphene_django.types import DjangoObjectType
from rescape_graphene import REQUIRE, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field
from rescape_graphene import increment_prop_until_unique
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.models import Location
from rescape_region.schema_models.scope.location.location_data_schema import LocationDataType, location_data_fields


def reverse_relationships():
    from rescape_region.schema_models.scope.project.project_schema import ProjectType, project_fields
    # Model a reverse relationship so we can get the locations of a project
    return dict(
        projects=dict(
            graphene_type=ProjectType,
            fields=R.omit(['locations'], project_fields),
            type_modifier=lambda *type_and_args: List(*type_and_args)
        )
    )


def raw_location_fields(with_reverse=True):
    return R.merge_all([
        dict(
            id=dict(create=DENY, update=REQUIRE),
            key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(Location, None, 'key', {})),
            name=dict(create=REQUIRE),
            # This refers to the LocationDataType, which is a representation of all the json fields of Location.data
            data=dict(
                graphene_type=LocationDataType,
                fields=location_data_fields,
                default=lambda: dict(),
                # type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
            ),
            # This is the OSM geojson
            geojson=dict(
                graphene_type=FeatureCollectionDataType,
                fields=feature_collection_data_type_fields,
                # type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
            )
        ),
        # Add reverse relationships if this is for location_schema, but don't if it's for project_schema
        reverse_relationships() if with_reverse else {},
        reversion_and_safe_delete_types
    ])

class LocationType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
    id = graphene.Int(source='pk')

    class Meta:
        model = Location

# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
LocationType._meta.fields['data'] = Field(
    LocationDataType,
    resolver=resolver_for_dict_field
)

# Modify the geojson field to use the geometry collection resolver
LocationType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)

location_fields_without_reverse = merge_with_django_properties(LocationType, raw_location_fields(False))

# This must be referenced in settings.py
location_schema_config = dict(
    model_class=Location,
    graphene_class=LocationType,
    graphene_fields=location_fields_without_reverse
)
