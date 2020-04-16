import graphene
from graphene import Field, Mutation, InputObjectType
from graphene_django.types import DjangoObjectType
from rescape_graphene import input_type_fields, REQUIRE, DENY, CREATE, \
    input_type_parameters_for_update_or_create, UPDATE, \
    guess_update_or_create, graphql_update_or_create, graphql_query, merge_with_django_properties, \
    resolver_for_dict_field
from rescape_region.models import GroupState
from rescape_region.schema_models.group_state_data_schema import GroupStateDataType, group_state_data_fields


def create_group_state_config(class_config):
    """
        Creates the GroupStateType based on specific class_config
    :param class_config: A dict containing class configurations. Right now it's only region in the form
    dict(
        region=dict(
            model_class=...,
            graphene_class=...,
            fields=...
        )
    )
    :return:
    """

    class GroupStateType(DjangoObjectType):
        """
            GroupStateType models GroupState, which represents the settings both imposed upon and chosen by the group
        """
        id = graphene.Int(source='pk')

        class Meta:
            model = GroupState

    # Modify data field to use the resolver.
    # I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
    # Django model to generate the fields
    GroupStateType._meta.fields['data'] = Field(GroupStateDataType(class_config), resolver=resolver_for_dict_field)

    group_state_fields = merge_with_django_properties(GroupStateType, dict(
        id=dict(create=DENY, update=REQUIRE),
        data=dict(graphene_type=GroupStateDataType(class_config), fields=group_state_data_fields(class_config),
                  default=lambda: dict())
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
    graphql_query_group_states = graphql_query(GroupStateType, group_state_fields, 'groupStates')

    return dict(
        model_class=GroupState,
        graphene_class=GroupStateType,
        graphene_fields=group_state_fields,
        create_mutation_class=CreateGroupState,
        update_mutation_class=UpdateGroupState,
        graphql_mutation=graphql_update_or_create_group_state,
        graphql_query=graphql_query_group_states
    )
