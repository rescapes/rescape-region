from graphene import Field, Mutation, InputObjectType
from graphene_django.types import DjangoObjectType
from rescape_graphene import input_type_fields, REQUIRE, DENY, CREATE, \
    input_type_parameters_for_update_or_create, UPDATE, \
    guess_update_or_create, graphql_update_or_create, graphql_query, merge_with_django_properties
from rescape_graphene import resolver
from rescape_region.models import GroupState
from rescape_region.schema_models import GroupStateDataType, group_state_data_fields


class GroupStateType(DjangoObjectType):
    """
        GroupStateType models GroupState, which represents the settings both imposed upon and chosen by the group
    """
    class Meta:
        model = GroupState


# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
GroupStateType._meta.fields['data'] = Field(GroupStateDataType, resolver=resolver('data'))


group_state_fields = merge_with_django_properties(GroupStateType, dict(
    id=dict(create=DENY, update=REQUIRE),
    data=dict(graphene_type=GroupStateDataType, fields=group_state_data_fields, default=lambda: dict())
))

group_state_mutation_config = dict(
    class_name='GroupState',
    crud={
        CREATE: 'createGroupState',
        UPDATE: 'updateGroupState'
    },
    resolve=guess_update_or_create
)


class UpsertGroupState(Mutation):
    """
        Abstract base class for mutation
    """
    group_state = Field(GroupStateType)

    def mutate(self, info, group_state_data=None):
        """
            Update or create the group state
        :param info:
        :param group_state_data:
        :return:
        """
        update_or_create_values = input_type_parameters_for_update_or_create(group_state_fields, group_state_data)
        # We can do update_or_create since we have a unique group_id in addition to the unique id
        group_state, created = GroupState.objects.update_or_create(**update_or_create_values)
        return UpsertGroupState(group_state=group_state)


class CreateGroupState(UpsertGroupState):
    """
        Create GroupState mutation class
    """

    class Arguments:
        group_state_data = type('CreateGroupStateInputType', (InputObjectType,),
                             input_type_fields(group_state_fields, CREATE, GroupStateType))(required=True)


class UpdateGroupState(UpsertGroupState):
    """
        Update GroupState mutation class
    """

    class Arguments:
        group_state_data = type('UpdateGroupStateInputType', (InputObjectType,),
                             input_type_fields(group_state_fields, UPDATE, GroupStateType))(required=True)


graphql_update_or_create_group_state = graphql_update_or_create(group_state_mutation_config, group_state_fields)
graphql_query_group_states = graphql_query('groupStates', group_state_fields)
