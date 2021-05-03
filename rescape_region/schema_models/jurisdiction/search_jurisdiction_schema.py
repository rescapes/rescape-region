from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType
from graphene_django.types import DjangoObjectType
from rescape_graphene import enforce_unique_props
from rescape_graphene import graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, FeatureCollectionDataType, \
    resolver_for_dict_field, create_paginated_type_mixin
from rescape_graphene.django_helpers.pagination import resolve_paginated_for_type, pagination_allowed_filter_arguments
from rescape_graphene.django_helpers.versioning import create_version_container_type, resolve_version_instance, \
    versioning_allowed_filter_arguments
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete, \
    update_or_create_with_revision, top_level_allowed_filter_arguments, fields_with_filter_fields, READ
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import DjangoObjectTypeRevisionedMixin

from rescape_region.schema_models.jurisdiction.jurisdiction_schema import jurisdiction_fields, \
    jurisdiction_versioned_fields, jurisdiction_paginated_fields
from rescape_region.schema_models.jurisdiction.search_jurisdiction_data_schema import SearchJurisdictionDataType
from rescape_region.models.search_jurisdiction import SearchJurisdiction


class SearchJurisdictionType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
    id = graphene.Int(source='pk')

    class Meta:
        model = SearchJurisdiction


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
search_jurisdiction_fields = fields_with_filter_fields(jurisdiction_fields, SearchJurisdictionType, crud=READ)

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
        **search_jurisdiction_fields
    )
    jurisdictions_paginated = Field(
        SearchJurisdictionPaginatedType,
        **pagination_allowed_filter_arguments(search_jurisdiction_paginated_fields, SearchJurisdictionPaginatedType)
    )
    search_jurisdictions_versioned = Field(
        SearchJurisdictionVersionedType,
        **versioning_allowed_filter_arguments(search_jurisdiction_versioned_fields, SearchJurisdictionVersionedType)
    )

    @staticmethod
    def _resolve_search_jurisdictions(info, **kwargs):
        return search_jurisdiction_resolver('filter', **kwargs)

    def resolve_search_jurisdictions(self, info, **kwargs):
        return search_jurisdiction_resolver(info, **kwargs)

    def resolve_search_jurisdictions_paginated(self, info, **kwargs):
        return resolve_paginated_for_type(
            SearchJurisdictionPaginatedType,
            SearchJurisdictionQuery._resolve_search_jurisdictions,
            **kwargs
        )

    def resolve_search_jurisdictions_versioned(self, info, **kwargs):
        """
            Get the version history of the jurisdiction matching the kwargs
        :param info:
        :param kwargs: id is the only thing required
        :return: A list of versions
        """
        return resolve_version_instance(SearchJurisdictionVersionedType, search_jurisdiction_resolver, **kwargs)


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
                jurisdiction_fields,
                CREATE,
                SearchJurisdictionType,
                create_filter_fields_for_search_type=True
            )
        )(required=True)


class UpdateSearchJurisdiction(UpsertSearchJurisdiction):
    """
        Update SearchJurisdiction mutation class
    """

    class Arguments:
        search_jurisdiction_data = type(
            'UpdateSearchJurisdictionInputType', (InputObjectType,),
            top_level_allowed_filter_arguments(
                jurisdiction_fields,
                UPDATE,
                SearchJurisdictionType,
                create_filter_fields_for_search_type=True)
        )(required=True)


class SearchJurisdictionMutation(graphene.ObjectType):
    create_search_jurisdiction = CreateSearchJurisdiction.Field()
    update_search_jurisdiction = UpdateSearchJurisdiction.Field()


graphql_update_or_create_jurisdiction = graphql_update_or_create(search_jurisdiction_mutation_config,
                                                                 search_jurisdiction_fields)
# Just use jurisdiction_fields, the search fields will be added automatically
graphql_query_jurisdictions = graphql_query(SearchJurisdictionType, jurisdiction_fields, 'searchJurisdictions')


def graphql_query_jurisdictions_limited(search_jurisdiction_fields):
    return graphql_query(SearchJurisdictionType, search_jurisdiction_fields, 'searchJurisdictions')


graphql_query_jurisdictions_paginated = graphql_query(
    SearchJurisdictionPaginatedType,
    jurisdiction_paginated_fields,
    'searchJurisdictionsPaginated'
)

graphql_query_search_jurisdictions_versioned = graphql_query(
    SearchJurisdictionVersionedType,
    jurisdiction_versioned_fields,
    'searchJurisdictionsVersioned'
)
