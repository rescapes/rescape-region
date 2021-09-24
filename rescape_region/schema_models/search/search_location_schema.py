import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType, List, String
from graphene_django.types import DjangoObjectType
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field
from rescape_graphene import enforce_unique_props
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete, \
    update_or_create_with_revision, ALLOW, top_level_allowed_filter_arguments, type_modify_fields
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.models import SearchJurisdiction
from rescape_region.models.search_location import SearchLocation
from rescape_region.schema_models.jurisdiction.search_jurisdiction_schema import SearchJurisdictionType, \
    search_jurisdiction_fields
from rescape_region.schema_models.location_street.search_location_street_data_schema import \
    SearchLocationStreetDataType, search_location_street_data_fields
from rescape_region.schema_models.scope.location.location_schema import location_fields
from rescape_region.schema_models.search.search_identification_data_type import SearchIdentificationDataType, \
    search_identification_fields
from rescape_region.schema_models.search.search_location_data_schema import SearchLocationDataType, \
    search_location_data_fields


class SearchLocationType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
    id = graphene.Int(source='pk')

    class Meta:
        model = SearchLocation


# Stores properties for searching by location id, such as identification.id = id1 or identification.idContains = [id1, id2]
SearchLocationType._meta.fields['identification'] = Field(
    SearchIdentificationDataType,
    resolver=resolver_for_dict_field
)

SearchLocationType._meta.fields['street'] = Field(
    SearchLocationStreetDataType,
    resolver=resolver_for_dict_field
)

# Modify the geojson field to use the geometry collection resolver
SearchLocationType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)

SearchLocationType._meta.fields['data'] = Field(
    SearchLocationDataType,
    resolver=resolver_for_dict_field
)

# Search Fields include the top level filter arguments, so
search_location_fields = merge_with_django_properties(
    SearchLocationType,
    dict(
        # The id of the SearchLocation (not the id search for the location)
        id=dict(create=DENY, update=REQUIRE),
        name=dict(type=String, related_input=ALLOW),

        # The id search properties, such as identification.id and identification.idContains
        identification=dict(
            graphene_type=SearchIdentificationDataType,
            fields=search_identification_fields,
            # Allow as related input as long as id so we can create/update search locations when saving search locations
            related_input=ALLOW
        ),

        # The street search properties, such as identification.id and identification.idContains
        street=dict(
            graphene_type=SearchLocationStreetDataType,
            fields=search_location_street_data_fields,
            # Allow as related input as long as id so we can create/update search locations when saving search locations
            related_input=ALLOW
        ),

        # The jurisdiction search properties, where each in the list is a jurisdiction scope
        jurisdictions=dict(
            graphene_type=SearchJurisdictionType,
            fields=search_jurisdiction_fields,
            # Allow as related input as long as id so we can create/update search locations when saving search locations
            related_input=ALLOW,
            type_modifier=lambda *type_and_args: List(*type_and_args)
        ),

        # This is the OSM geojson for the search_location
        geojson=dict(
            # TODO Do we need a SearchFeatureCollectionDataType?
            graphene_type=FeatureCollectionDataType,
            fields=feature_collection_data_type_fields,
            # Allow as related input as long as id so we can create/update search locations when saving search locations
            related_input=ALLOW
        ),

        data=dict(
            graphene_type=SearchLocationDataType,
            type=SearchLocationDataType,
            fields=search_location_data_fields,
            default=lambda: dict(streets=[]),
            # Allow as related input as long as id so we can create/update search_locations when saving search locations
            related_input=ALLOW
        ),
        **reversion_and_safe_delete_types
    )
)


class SearchLocationQuery(ObjectType):
    search_locations = graphene.List(
        SearchLocationType,
        **top_level_allowed_filter_arguments(search_location_fields, SearchLocationType)
    )

    @staticmethod
    def _resolve_search_locations(info, **kwargs):
        # TODO for use with versioning, pagination
        return search_location_resolver('filter', **kwargs)

    def resolve_search_locations(self, info, **kwargs):
        return search_location_resolver('filter', **kwargs)


def search_location_resolver(manager_method, **kwargs):
    """

    Resolves the search locations for model get_location_model()
    :param manager_method: 'filter', 'get', or 'count'
    :param kwargs: Filter arguments for the SearchLocation
    :return:
    """

    q_expressions = process_filter_kwargs(SearchLocation, **kwargs)
    return getattr(SearchLocation.objects, manager_method)(
        *q_expressions
    )


search_location_mutation_config = dict(
    class_name='SearchLocation',
    crud={
        CREATE: 'createSearchLocation',
        UPDATE: 'updateSearchLocation'
    },
    resolve=guess_update_or_create
)


class UpsertSearchLocation(Mutation):
    """
        Abstract base class for mutation
    """
    search_location = Field(SearchLocationType)

    @transaction.atomic
    def mutate(self, info, search_location_data=None):
        deleted_search_location_response = delete_if_marked_for_delete(
            SearchLocation, UpsertSearchLocation, 'search_location',
            search_location_data
        )
        if deleted_search_location_response:
            return deleted_search_location_response

        modified_search_location_data = R.compose(
            # Make sure that all props are unique that must be, either by modifying values or erring.
            lambda data: enforce_unique_props(search_location_fields, data),
            # Remove the many to many values. They are saved separately
            lambda data: R.omit(
                ['jurisdictions'],
                data
            )
        )(search_location_data)

        update_or_create_values = input_type_parameters_for_update_or_create(search_location_fields,
                                                                             modified_search_location_data)
        search_location, created = update_or_create_with_revision(SearchLocation, update_or_create_values)

        # SearchJurisdictions can be created during the creation of search_locations
        if R.prop_or(False, 'jurisdictions', search_location_data):
            existing_search_intersections_by_id = R.index_by(R.prop('id'), search_location.jurisdictions.all())
            for search_jurisdiction_unsaved in R.prop('intersections', search_location_data):
                # existing instances have an id
                search_jursidiction_id = R.prop_or(None, 'id', search_jurisdiction_unsaved)
                search_jurisdiction, created = update_or_create_with_revision(
                    SearchJurisdiction,
                    R.merge(
                        R.prop(search_jursidiction_id, existing_search_intersections_by_id) if search_jursidiction_id else {},
                        search_jurisdiction_unsaved
                    )
                )
                # Once saved, add it to the search location
                search_location.jurisdictions.set(search_jurisdiction)

        return UpsertSearchLocation(search_location=search_location)


class CreateSearchLocation(UpsertSearchLocation):
    """
        Create SearchLocation mutation class
    """

    class Arguments:
        search_location_data = type(
            'CreateSearchLocationInputType', (InputObjectType,),
            input_type_fields(
                search_location_fields,
                CREATE,
                SearchLocationType
            )
        )(required=True)


class UpdateSearchLocation(UpsertSearchLocation):
    """
        Update SearchLocation mutation class
    """

    class Arguments:
        search_location_data = type(
            'UpdateSearchLocationInputType', (InputObjectType,),
            input_type_fields(
                search_location_fields,
                UPDATE,
                SearchLocationType
            )
        )(required=True)


class SearchLocationMutation(graphene.ObjectType):
    create_search_location = CreateSearchLocation.Field()
    update_search_location = UpdateSearchLocation.Field()


graphql_update_or_create_search_location = graphql_update_or_create(search_location_mutation_config,
                                                                    search_location_fields)
# Just use location fields here, the search fields will be added automatically
graphql_query_search_locations = graphql_query(SearchLocationType, search_location_fields, 'searchLocations')


def graphql_query_locations_limited(search_location_fields):
    return graphql_query(SearchLocationType, search_location_fields, 'searchLocations')


# This must be referenced in settings.py
search_location_schema_config = dict(
    model_class=SearchLocation,
    graphene_class=SearchLocationType,
    graphene_fields=search_location_fields,
    query=SearchLocationQuery,
    mutation=SearchLocationMutation
)
