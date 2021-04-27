import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, increment_prop_until_unique
from rescape_graphene import enforce_unique_props
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, update_or_create_with_revision, \
    top_level_allowed_filter_arguments
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_python_helpers import ramda as R

from rescape_region.helpers.sankey_helpers import add_sankey_graph_to_resource_dict
from rescape_region.models.resource import Resource
from rescape_region.schema_models.scope.region.region_schema import RegionType
from rescape_region.schema_models.resource_data_schema import ResourceDataType, resource_data_fields


class ResourceType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
    id = graphene.Int(source='pk')

    class Meta:
        model = Resource


raw_resource_fields = merge_with_django_properties(ResourceType, dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(Resource, None, 'key', R.pick(['deleted']))),
    name=dict(create=REQUIRE),
    # This refers to the Resource, which is a representation of all the json fields of Resource.data
    data=dict(graphene_type=ResourceDataType, fields=resource_data_fields, default=lambda: dict()),
    # This is a Foreign Key. Graphene generates these relationships for us, but we need it here to
    # support our Mutation subclasses and query_argument generation
    # For simplicity we limit fields to id. Mutations can only us id, and a query doesn't need other
    # details of the resource--it can query separately for that
    region=dict(graphene_type=RegionType,
                fields=merge_with_django_properties(RegionType, dict(id=dict(create=REQUIRE)))),
    **reversion_and_safe_delete_types
))

# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
ResourceType._meta.fields['data'] = Field(
    ResourceDataType,
    resolver=resolver_for_dict_field
)

# Modify the geojson field to use the geometry collection resolver
ResourceType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)
resource_fields = merge_with_django_properties(ResourceType, raw_resource_fields)


class ResourceQuery(ObjectType):
    id = graphene.Int(source='pk')

    resources = graphene.List(
        ResourceType,
        **top_level_allowed_filter_arguments(resource_fields, ResourceType)
    )

    @login_required
    def resolve_resources(self, info, **kwargs):
        q_expressions = process_filter_kwargs(Resource, **R.merge(dict(deleted__isnull=True), kwargs))

        return Resource.objects.filter(
            *q_expressions
        )


resource_mutation_config = dict(
    class_name='Resource',
    crud={
        CREATE: 'createResource',
        UPDATE: 'updateResource'
    },
    resolve=guess_update_or_create
)


class UpsertResource(Mutation):
    """
        Abstract base class for mutation
    """
    resource = Field(ResourceType)

    @transaction.atomic
    @login_required
    def mutate(self, info, resource_data=None):
        # We must merge in existing resource.data if we are updating
        if R.has('id', resource_data):
            # New data gets priority, but this is a deep merge.
            resource_data['data'] = R.merge_deep(
                Resource.objects.get(id=resource_data['id']).data,
                R.prop_or({}, 'data', resource_data)
            )
            # Modifies defaults value to add .data.graph
            # We could decide in the future to generate this derived data on the client, but it's easy enough to do here

        modified_resource_data = enforce_unique_props(resource_fields, resource_data)
        # Make sure that all props are unique that must be, either by modifying values or erring.
        update_or_create_values = input_type_parameters_for_update_or_create(resource_fields, modified_resource_data)

        # Add the sankey data unless we are updating the instance without updating instance.data
        update_or_create_values_with_sankey_data = R.merge(update_or_create_values, dict(
            defaults=add_sankey_graph_to_resource_dict(
                update_or_create_values['defaults']
            )
        )) if R.has('defaults', update_or_create_values) else update_or_create_values

        resource, created = update_or_create_with_revision(Resource, update_or_create_values_with_sankey_data)
        return UpsertResource(resource=resource)


class CreateResource(UpsertResource):
    """
        Create Resource mutation class
    """

    class Arguments:
        resource_data = type('CreateResourceInputType', (InputObjectType,),
                             input_type_fields(resource_fields, CREATE, ResourceType))(required=True)


class UpdateResource(UpsertResource):
    """
        Update Resource mutation class
    """

    class Arguments:
        resource_data = type('UpdateResourceInputType', (InputObjectType,),
                             input_type_fields(resource_fields, UPDATE, ResourceType))(required=True)


class ResourceMutation(graphene.ObjectType):
    create_resource = CreateResource.Field()
    update_resource = UpdateResource.Field()


graphql_update_or_create_resource = graphql_update_or_create(resource_mutation_config, resource_fields)
graphql_query_resources = graphql_query(ResourceType, resource_fields, 'resources')
