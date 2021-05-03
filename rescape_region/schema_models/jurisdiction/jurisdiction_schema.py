from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType
from graphene_django.types import DjangoObjectType
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, create_paginated_type_mixin
from rescape_graphene import enforce_unique_props
from rescape_graphene.django_helpers.pagination import resolve_paginated_for_type, pagination_allowed_filter_arguments
from rescape_graphene.django_helpers.versioning import create_version_container_type, resolve_version_instance, \
    versioning_allowed_filter_arguments
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete, \
    update_or_create_with_revision, ALLOW, top_level_allowed_filter_arguments
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields

from rescape_region.schema_models.jurisdiction.jurisdiction_data_schema import JurisdictionDataType, \
    jurisdiction_data_fields
from rescape_region.models.jurisdiction import Jurisdiction


class JurisdictionType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
    id = graphene.Int(source='pk')

    class Meta:
        model = Jurisdiction


# Modify the geojson field to use the geometry collection resolver
JurisdictionType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)

JurisdictionType._meta.fields['data'] = Field(
    JurisdictionDataType,
    resolver=resolver_for_dict_field
)

jurisdiction_fields = merge_with_django_properties(JurisdictionType, dict(
    id=dict(create=DENY, update=REQUIRE),

    # This is the OSM geojson for the jurisdiction
    geojson=dict(
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields,
        # Allow geojson as related input as long as id so we can create/update jurisdictions when saving locations
        related_input=ALLOW
    ),

    data=dict(
        graphene_type=JurisdictionDataType,
        fields=jurisdiction_data_fields,
        default=lambda: dict(streets=[]),
        # Allow data as related input as long as id so we can create/update jurisdictions when saving locations
        related_input=ALLOW
    ),
    **reversion_and_safe_delete_types
))

# Paginated version of JurisdictionType
(JurisdictionPaginatedType, jurisdiction_paginated_fields) = itemgetter('type', 'fields')(
    create_paginated_type_mixin(JurisdictionType, jurisdiction_fields)
)

# Revision version of JurisdictionType
(JurisdictionVersionedType, jurisdiction_versioned_fields) = itemgetter('type', 'fields')(
    create_version_container_type(JurisdictionType, jurisdiction_fields)
)

class JurisdictionQuery(ObjectType):
    jurisdictions = graphene.List(
        JurisdictionType,
        **top_level_allowed_filter_arguments(jurisdiction_fields, JurisdictionType)
    )
    jurisdictions_paginated = Field(
        JurisdictionPaginatedType,
        **pagination_allowed_filter_arguments(jurisdiction_paginated_fields, JurisdictionPaginatedType)
    )
    jurisdictions_versioned = Field(
        JurisdictionVersionedType,
        **versioning_allowed_filter_arguments(jurisdiction_versioned_fields, JurisdictionVersionedType)
    )

    @staticmethod
    def _resolve_jurisdictions(info, **kwargs):
        return jurisdiction_resolver('filter', **kwargs)

    def resolve_jurisdictions(self, info, **kwargs):
        return jurisdiction_resolver(info, **kwargs)

    def resolve_jurisdictions_paginated(self, info, **kwargs):
        return resolve_paginated_for_type(
            JurisdictionPaginatedType,
            JurisdictionQuery._resolve_jurisdictions,
            **kwargs
        )

    def resolve_jurisdictions_versioned(self, info, **kwargs):
        """
            Get the version history of the jurisdiction matching the kwargs
        :param info:
        :param kwargs: id is the only thing required
        :return: A list of versions
        """
        return resolve_version_instance(JurisdictionVersionedType, jurisdiction_resolver, **kwargs)


def jurisdiction_resolver(manager_method, **kwargs):
    """

    Resolves the jurisdictions for model get_jurisdiction_model()
    :param manager_method: 'filter', 'get', or 'count'
    :param kwargs: Filter arguments for the Jurisdiction
    :return:
    """

    q_expressions = process_filter_kwargs(Jurisdiction, **kwargs)
    return getattr(Jurisdiction.objects, manager_method)(
        *q_expressions
    )


jurisdiction_mutation_config = dict(
    class_name='Jurisdiction',
    crud={
        CREATE: 'createJurisdiction',
        UPDATE: 'updateJurisdiction'
    },
    resolve=guess_update_or_create
)


class UpsertJurisdiction(Mutation):
    """
        Abstract base class for mutation
    """
    jurisdiction = Field(JurisdictionType)

    @transaction.atomic
    def mutate(self, info, jurisdiction_data=None):
        deleted_jurisdiction_response = delete_if_marked_for_delete(
            Jurisdiction, UpsertJurisdiction, 'jurisdiction',
            jurisdiction_data
        )
        if deleted_jurisdiction_response:
            return deleted_jurisdiction_response

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_jurisdiction_data = enforce_unique_props(jurisdiction_fields, jurisdiction_data)
        update_or_create_values = input_type_parameters_for_update_or_create(jurisdiction_fields,
                                                                             modified_jurisdiction_data)
        jurisdiction, created = update_or_create_with_revision(Jurisdiction, update_or_create_values)

        return UpsertJurisdiction(jurisdiction=jurisdiction)


class CreateJurisdiction(UpsertJurisdiction):
    """
        Create Jurisdiction mutation class
    """

    class Arguments:
        jurisdiction_data = type('CreateJurisdictionInputType', (InputObjectType,),
                                 input_type_fields(jurisdiction_fields, CREATE, JurisdictionType))(required=True)


class UpdateJurisdiction(UpsertJurisdiction):
    """
        Update Jurisdiction mutation class
    """

    class Arguments:
        jurisdiction_data = type('UpdateJurisdictionInputType', (InputObjectType,),
                                 input_type_fields(jurisdiction_fields, UPDATE, JurisdictionType))(required=True)


class JurisdictionMutation(graphene.ObjectType):
    create_jurisdiction = CreateJurisdiction.Field()
    update_jurisdiction = UpdateJurisdiction.Field()


graphql_update_or_create_jurisdiction = graphql_update_or_create(jurisdiction_mutation_config, jurisdiction_fields)
graphql_query_jurisdictions = graphql_query(JurisdictionType, jurisdiction_fields, 'jurisdictions')


def graphql_query_jurisdictions_limited(jurisdiction_fields):
    return graphql_query(JurisdictionType, jurisdiction_fields, 'jurisdictions')


graphql_query_jurisdictions_paginated = graphql_query(
    JurisdictionPaginatedType,
    jurisdiction_paginated_fields,
    'jurisdictionsPaginated'
)

graphql_query_jurisdictions_versioned = graphql_query(
    JurisdictionVersionedType,
    jurisdiction_versioned_fields,
    'jurisdictionsVersioned'
)
