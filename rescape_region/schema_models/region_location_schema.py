from copy import deepcopy

import graphene
from django.db import transaction
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from graphene import InputObjectType, Mutation, Field
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R
from rescape_graphene import increment_prop_until_unique, enforce_unique_props

from rescape_region.models import RegionLocation
from .location_data_schema import RegionLocationDataType, region_location_data_fields

raw_location_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(RegionLocation, None, 'key')),
    name=dict(create=REQUIRE),
    created_at=dict(),
    updated_at=dict(),
    # This refers to the RegionLocationDataType, which is a representation of all the json fields of Location.data
    data=dict(graphene_type=RegionLocationDataType, fields=region_location_data_fields, default=lambda: dict()),
    # This is the OSM geojson
    geojson=dict(
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields
    )
)


class RegionLocationType(DjangoObjectType):

    class Meta:
        model = RegionLocation


# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
RegionLocationType._meta.fields['data'] = Field(RegionLocationDataType, resolver=resolver_for_dict_field)

# Modify the geojson field to use the geometry collection resolver
RegionLocationType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)
location_fields = merge_with_django_properties(RegionLocationType, raw_location_fields)

location_mutation_config = dict(
    class_name='Location',
    crud={
        CREATE: 'createLocation',
        UPDATE: 'updateLocation'
    },
    resolve=guess_update_or_create
)


class UpsertLocation(Mutation):
    """
        Abstract base class for mutation
    """
    location = Field(RegionLocationType)

    @transaction.atomic
    @login_required
    def mutate(self, info, location_data=None):
        # We must merge in existing location.data if we are updating data
        if R.has('id', location_data) and R.has('data', location_data):
            # New data gets priority, but this is a deep merge.
            location_data['data'] = R.merge_deep(
                RegionLocation.objects.get(id=location_data['id']).data,
                location_data['data']
            )

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_location_data = enforce_unique_props(location_fields, location_data)
        update_or_create_values = input_type_parameters_for_update_or_create(location_fields, modified_location_data)

        location, created = RegionLocation.objects.update_or_create(**update_or_create_values)
        return UpsertLocation(location=location)


class CreateLocation(UpsertLocation):
    """
        Create Location mutation class
    """

    class Arguments:
        location_data = type('CreateLocationInputType', (InputObjectType,),
                             input_type_fields(location_fields, CREATE, RegionLocationType))(required=True)


class UpdateLocation(UpsertLocation):
    """
        Update Location mutation class
    """

    class Arguments:
        location_data = type('UpdateLocationInputType', (InputObjectType,),
                             input_type_fields(location_fields, UPDATE, RegionLocationType))(required=True)


graphql_update_or_create_region_location = graphql_update_or_create(location_mutation_config, location_fields)
graphql_query_region_locations = graphql_query(RegionLocationType, location_fields, 'locations')
