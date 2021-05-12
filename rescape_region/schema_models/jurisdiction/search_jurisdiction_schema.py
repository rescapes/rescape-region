from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType, Int
from graphene_django.types import DjangoObjectType
from rescape_graphene import enforce_unique_props
from rescape_graphene import graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, FeatureCollectionDataType, \
    resolver_for_dict_field, create_paginated_type_mixin
from rescape_graphene.django_helpers.pagination import resolve_paginated_for_type, pagination_allowed_filter_arguments
from rescape_graphene.django_helpers.versioning import create_version_container_type, resolve_version_instance, \
    versioning_allowed_filter_arguments
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete, \
    update_or_create_with_revision, top_level_allowed_filter_arguments, fields_with_filter_fields, READ, \
    merge_with_django_properties, DENY, REQUIRE, ALLOW, type_modify_fields
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import DjangoObjectTypeRevisionedMixin, \
    reversion_and_safe_delete_types
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields

from rescape_region.schema_models.jurisdiction.jurisdiction_data_schema import jurisdiction_data_fields
from rescape_region.schema_models.jurisdiction.jurisdiction_schema import jurisdiction_fields, \
    jurisdiction_versioned_fields, jurisdiction_paginated_fields
from rescape_region.schema_models.jurisdiction.search_jurisdiction_data_schema import SearchJurisdictionDataType, \
    search_jurisdiction_data_fields
from rescape_region.models.search_jurisdiction import SearchJurisdiction

from rescape_python_helpers import ramda as R, memoize

raw_search_jurisdiction_fields = lambda add_filter=lambda *args, **kwargs: args[0]: dict(
    # The id of the SearchJurisidiction (not the id search for the Jursidiction)
    id=dict(type=Int, create=DENY, update=REQUIRE),

    # This is the OSM geojson for the search_location
    geojson=dict(
        # TODO Do we need a SearchFeatureCollectionDataType?
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields,
        related_input=ALLOW
    ),

    data=dict(
        graphene_type=SearchJurisdictionDataType,
        type=SearchJurisdictionDataType,
        fields=add_filter(jurisdiction_data_fields, SearchJurisdictionDataType,
                          create_filter_fields_for_search_type=True),
        default=lambda: dict(streets=[]),
        # Allow as related input as long as id so we can create/update search_locations when saving search locations
        related_input=ALLOW
    ),
    **reversion_and_safe_delete_types
)


@memoize()
def create_search_jurisdiction_type(class_name):
    return type(
        class_name, (DjangoObjectType, DjangoObjectTypeRevisionedMixin),
        R.merge_all([
            dict(id=graphene.Int(source='pk')),
            type_modify_fields(raw_search_jurisdiction_fields(fields_with_filter_fields)),
            dict(Meta=type('Meta', (object,), dict(model=SearchJurisdiction)))
        ])
    )


SearchJurisdictionType = create_search_jurisdiction_type('SearchJurisdictionType')

# Modify the geojson field to use the geometry collection resolver
SearchJurisdictionType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)
SearchJurisdictionType._meta.fields['data'] = Field(
    SearchJurisdictionDataType,
    resolver=resolver_for_dict_field
)

# Search Fields include the top level filter arguments, so
search_jurisdiction_fields = merge_with_django_properties(
    SearchJurisdictionType,
    raw_search_jurisdiction_fields(fields_with_filter_fields)
)

# Paginated version of SearchJurisdictionType
(SearchJurisdictionPaginatedType, search_jurisdiction_paginated_fields) = itemgetter('type', 'fields')(
    # Filter fields are added by caller, so use jurisdiction_fields, not search_jurisdiction_fields
    create_paginated_type_mixin(SearchJurisdictionType, jurisdiction_fields)
)

# Revision version of SearchJurisdictionType
(SearchJurisdictionVersionedType, search_jurisdiction_versioned_fields) = itemgetter('type', 'fields')(
    # Filter fields are added by caller, so use jurisdiction_fields, not search_jurisdiction_field
    create_version_container_type(SearchJurisdictionType, jurisdiction_fields)
)


class SearchJurisdictionQuery(ObjectType):
    jurisdictions = graphene.List(
        SearchJurisdictionType,
        **top_level_allowed_filter_arguments(
            raw_search_jurisdiction_fields(fields_with_filter_fields),
            SearchJurisdictionType,
            # fields_with_filter_fields puts filters on inner props. We don't want filters top-level
            with_filter_fields=False
        )
    )

    @staticmethod
    def _resolve_search_jurisdictions(info, **kwargs):
        return search_jurisdiction_resolver('filter', **kwargs)

    def resolve_search_jurisdictions(self, info, **kwargs):
        return search_jurisdiction_resolver(info, **kwargs)


def search_jurisdiction_resolver(manager_method, **kwargs):
    """

    Resolves the jurisdictions for model get_jurisdiction_model()
    :param manager_method: 'filter', 'get', or 'count'
    :param kwargs: Filter arguments for the SearchJurisdiction
    :return:
    """

    q_expressions = process_filter_kwargs(SearchJurisdiction, **kwargs)
    return getattr(SearchJurisdiction.objects, manager_method)(
        *q_expressions
    )


search_jurisdiction_mutation_config = dict(
    class_name='SearchJurisdiction',
    crud={
        CREATE: 'createSearchJurisdiction',
        UPDATE: 'updateSearchJurisdiction'
    },
    resolve=guess_update_or_create
)


class UpsertSearchJurisdiction(Mutation):
    """
        Abstract base class for mutation
    """
    search_jurisdiction = Field(SearchJurisdictionType)

    @transaction.atomic
    def mutate(self, info, search_jurisdiction_data=None):
        deleted_search_jurisdiction_response = delete_if_marked_for_delete(
            SearchJurisdiction, UpsertSearchJurisdiction, 'searchJurisdiction',
            search_jurisdiction_data
        )
        if deleted_search_jurisdiction_response:
            return deleted_search_jurisdiction_response

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_search_jurisdiction_data = enforce_unique_props(search_jurisdiction_fields, search_jurisdiction_data)
        update_or_create_values = input_type_parameters_for_update_or_create(search_jurisdiction_fields,
                                                                             modified_search_jurisdiction_data)
        search_jurisdiction, created = update_or_create_with_revision(SearchJurisdiction, update_or_create_values)

        return UpsertSearchJurisdiction(search_jurisdiction=search_jurisdiction)


class CreateSearchJurisdiction(UpsertSearchJurisdiction):
    """
        Create SearchJurisdiction mutation class
    """

    class Arguments:
        search_jurisdiction_data = type(
            'CreateSearchJurisdictionInputType',
            (InputObjectType,),
            input_type_fields(
                search_jurisdiction_fields,
                CREATE,
                SearchJurisdictionType,
                with_filter_fields=False
            )
        )(required=True)


class UpdateSearchJurisdiction(UpsertSearchJurisdiction):
    """
        Update SearchJurisdiction mutation class
    """

    class Arguments:
        search_jurisdiction_data = type(
            'UpdateSearchJurisdictionInputType', (InputObjectType,),
            input_type_fields(
                search_jurisdiction_fields,
                UPDATE,
                SearchJurisdictionType,
                with_filter_fields=False
            )
        )(required=True)


class SearchJurisdictionMutation(graphene.ObjectType):
    create_search_jurisdiction = CreateSearchJurisdiction.Field()
    update_search_jurisdiction = UpdateSearchJurisdiction.Field()


graphql_update_or_create_jurisdiction = graphql_update_or_create(search_jurisdiction_mutation_config,
                                                                 search_jurisdiction_fields)
# Just use jurisdiction_fields, the search fields will be added automatically
graphql_query_jurisdictions = graphql_query(SearchJurisdictionType, search_jurisdiction_fields, 'searchJurisdictions')


def graphql_query_jurisdictions_limited(search_jurisdiction_fields):
    return graphql_query(SearchJurisdictionType, search_jurisdiction_fields, 'searchJurisdictions')
