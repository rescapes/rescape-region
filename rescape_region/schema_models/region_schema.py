from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, allowed_filter_arguments, create_paginated_type_mixin, \
    get_paginator
from rescape_graphene import increment_prop_until_unique, enforce_unique_props
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.model_helpers import get_region_model
from rescape_region.models.region import Region
from .region_data_schema import RegionDataType, region_data_fields

raw_region_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(Region, None, 'key', {})),
    name=dict(create=REQUIRE),
    created_at=dict(),
    updated_at=dict(),
    # This refers to the RegionDataType, which is a representation of all the json fields of Region.data
    data=dict(graphene_type=RegionDataType, fields=region_data_fields, default=lambda: dict()),
    # This is the OSM geojson
    geojson=dict(
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields
    ),
    # TODO this needs special authentication to perform writes of deleted=True or reads of deleted=True
    deleted=dict(),
)


class RegionType(DjangoObjectType):
    id = graphene.Int(source='pk')

    class Meta:
        model = get_region_model()

# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
RegionType._meta.fields['data'] = Field(RegionDataType, resolver=resolver_for_dict_field)

# Modify the geojson field to use the geometry collection resolver
RegionType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)
region_fields = merge_with_django_properties(RegionType, raw_region_fields)


# Paginated version of ProjectType
(RegionPaginatedType, region_paginated_fields) = itemgetter('type', 'fields')(
    create_paginated_type_mixin(RegionType, region_fields)
)


class RegionQuery(ObjectType):
    regions = graphene.List(
        RegionType,
        **allowed_filter_arguments(region_fields, RegionType)
    )
    regions_paginated = Field(
        RegionPaginatedType,
        **allowed_filter_arguments(region_paginated_fields, RegionPaginatedType)
    )

    @login_required
    def resolve_regions(self, info, **kwargs):
        return region_resolver('filter', **kwargs)

    @login_required
    def resolve_regions_paginated(self, info, **kwargs):
        regions = region_resolver('filter', **R.prop_or({}, 'objects', kwargs)).order_by('id')
        return get_paginator(
            regions,
            R.prop('page_size', kwargs),
            R.prop('page', kwargs),
            RegionPaginatedType
        )


def region_resolver(manager_method, **kwargs):
    """

    Resolves the regions for model get_region_model()
    :param manager_method: 'filter', 'get', or 'count'
    :param kwargs: Filter arguments for the Region
    :return:
    """

    q_expressions = process_filter_kwargs(get_region_model(), kwargs)
    return getattr(get_region_model().objects, manager_method)(
        *q_expressions
    )

region_mutation_config = dict(
    class_name='Region',
    crud={
        CREATE: 'createRegion',
        UPDATE: 'updateRegion'
    },
    resolve=guess_update_or_create
)


class UpsertRegion(Mutation):
    """
        Abstract base class for mutation
    """
    region = Field(RegionType)


    @transaction.atomic
    @login_required
    def mutate(self, info, region_data=None):

        deleted_region_response = delete_if_marked_for_delete(Region, UpsertRegion, 'region', region_data)
        if deleted_region_response:
            return deleted_region_response

        # We must merge in existing region.data if we are updating data
        if R.has('id', region_data) and R.has('data', region_data):
            # New data gets priority, but this is a deep merge.
            region_data['data'] = R.merge_deep(
                Region.objects.get(id=region_data['id']).data,
                region_data['data']
            )

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_region_data = enforce_unique_props(region_fields, region_data)
        update_or_create_values = input_type_parameters_for_update_or_create(region_fields, modified_region_data)
        region, created = Region.objects.update_or_create(**update_or_create_values)
        return UpsertRegion(region=region)


class CreateRegion(UpsertRegion):
    """
        Create Region mutation class
    """

    class Arguments:
        region_data = type('CreateRegionInputType', (InputObjectType,),
                           input_type_fields(region_fields, CREATE, RegionType))(required=True)


class UpdateRegion(UpsertRegion):
    """
        Update Region mutation class
    """

    class Arguments:
        region_data = type('UpdateRegionInputType', (InputObjectType,),
                           input_type_fields(region_fields, UPDATE, RegionType))(required=True)


class RegionMutation(graphene.ObjectType):
    create_region = CreateRegion.Field()
    update_region = UpdateRegion.Field()

graphql_update_or_create_region = graphql_update_or_create(region_mutation_config, region_fields)
graphql_query_regions = graphql_query(RegionType, region_fields, 'regions')


def graphql_query_regions_limited(region_fields):
    return graphql_query(RegionType, region_fields, 'regions')


graphql_query_regions_paginated = graphql_query(
    RegionPaginatedType,
    region_paginated_fields,
    'regionsPaginated'
)
