from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, create_paginated_type_mixin
from rescape_graphene import increment_prop_until_unique, enforce_unique_props
from rescape_graphene.django_helpers.pagination import resolve_paginated_for_type, pagination_allowed_filter_arguments
from rescape_graphene.graphql_helpers.schema_helpers import update_or_create_with_revision, \
    top_level_allowed_filter_arguments, delete_if_marked_for_delete, \
    query_with_filter_and_order_kwargs
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.models import Location
# This file is only used for tests in rescape_region
from rescape_region.schema_models.scope.location.location_data_schema import LocationDataType, location_data_fields

raw_location_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(Location, None, 'key', {})),
    name=dict(create=REQUIRE),
    # This refers to the LocationDataType, which is a representation of all the json fields of Location.data
    data=dict(
        graphene_type=LocationDataType,
        fields=location_data_fields,
        default=lambda: dict(),
        #type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    ),
    # This is the OSM geojson
    geojson=dict(
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields,
        #type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    ),
    **reversion_and_safe_delete_types
)


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
location_fields = merge_with_django_properties(LocationType, raw_location_fields)

# Paginated version of LocationType
(LocationPaginatedType, location_paginated_fields) = itemgetter('type', 'fields')(
    create_paginated_type_mixin(LocationType, location_fields)
)


class LocationQuery(ObjectType):
    locations = graphene.List(
        LocationType,
        **top_level_allowed_filter_arguments(location_fields, LocationType)
    )
    locations_paginated = Field(
        LocationPaginatedType,
        **pagination_allowed_filter_arguments(location_paginated_fields, LocationPaginatedType)
    )

    @staticmethod
    def _resolve_locations(info, **kwargs):
        # Default to not deleted, it can be overridden by kwargs
        return query_with_filter_and_order_kwargs(Location, **R.merge(dict(deleted__isnull=True), kwargs))

    @login_required
    def resolve_locations(self, info, **kwargs):
        return LocationQuery._resolve_locations(info, **kwargs)

    @login_required
    def resolve_locations_paginated(self, info, **kwargs):
        return resolve_paginated_for_type(
            LocationPaginatedType,
            LocationQuery._resolve_locations,
            **kwargs
        )


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
    location = Field(LocationType)

    @transaction.atomic
    @login_required
    def mutate(self, info, location_data=None):
        with transaction.atomic():
            deleted_location_response = delete_if_marked_for_delete(Location, UpsertLocation, 'location', location_data)
            if deleted_location_response:
                return deleted_location_response

            # We must merge in existing location.data if we are updating data
            if R.has('id', location_data) and R.has('data', location_data):
                # New data gets priority, but this is a deep merge.
                location_data['data'] = R.merge_deep(
                    Location.objects.get(id=location_data['id']).data,
                    location_data['data']
                )

            # Make sure that all props are unique that must be, either by modifying values or erring.
            modified_location_data = enforce_unique_props(location_fields, location_data)
            update_or_create_values = input_type_parameters_for_update_or_create(location_fields, modified_location_data)

            location, created = update_or_create_with_revision(Location, update_or_create_values)
            return UpsertLocation(location=location)


class CreateLocation(UpsertLocation):
    """
        Create Location mutation class
    """

    class Arguments:
        location_data = type('CreateLocationInputType', (InputObjectType,),
                             input_type_fields(location_fields, CREATE, LocationType))(required=True)


class UpdateLocation(UpsertLocation):
    """
        Update Location mutation class
    """

    class Arguments:
        location_data = type('UpdateLocationInputType', (InputObjectType,),
                             input_type_fields(location_fields, UPDATE, LocationType))(required=True)


class LocationMutation(graphene.ObjectType):
    create_location = CreateLocation.Field()
    update_location = UpdateLocation.Field()


graphql_update_or_create_location = graphql_update_or_create(location_mutation_config, location_fields)
graphql_query_locations = graphql_query(LocationType, location_fields, 'locations')

# This must be referenced in settings.py
location_schema_config = dict(
    model_class=Location,
    graphene_class=LocationType,
    graphene_fields=location_fields,
    query=LocationQuery,
    mutation=LocationMutation
)

graphql_query_locations_paginated = graphql_query(
    LocationPaginatedType,
    location_paginated_fields,
    'locationsPaginated'
)
