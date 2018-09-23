from graphene import Field, Mutation, InputObjectType
from graphene_django.types import DjangoObjectType
from rescape_graphene import input_type_fields, REQUIRE, DENY, CREATE, \
    input_type_parameters_for_update_or_create, UPDATE, \
    guess_update_or_create, graphql_update_or_create, graphql_query, merge_with_django_properties, UserType
from rescape_graphene import resolver
from rescape_region.models import UserState
from rescape_region.schema_models import UserStateDataType, user_state_data_fields


class UserStateType(DjangoObjectType):
    """
        UserStateType models UserState, which represents the settings both imposed upon and chosen by the user
    """
    class Meta:
        model = UserState


# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
UserStateType._meta.fields['data'] = Field(UserStateDataType, resolver=resolver('data'))

user_state_fields = merge_with_django_properties(UserStateType, dict(
    id=dict(create=DENY, update=REQUIRE),
    # This is a Foreign Key. Graphene generates these relationships for us, but we need it here to
    # support our Mutation subclasses and query_argument generation
    # For simplicity we limit fields to id. Mutations can only use id, and a query doesn't need other
    # details of the User--it can query separately for that
    user=dict(graphene_type=UserType, fields=merge_with_django_properties(UserType, dict(id=dict(create=REQUIRE)))),
    # This refers to the UserState, which is a representation of all the json fields of UserState.data
    data=dict(graphene_type=UserStateDataType, fields=user_state_data_fields, default=lambda: dict())
))

user_state_mutation_config = dict(
    class_name='UserState',
    crud={
        CREATE: 'createUserState',
        UPDATE: 'updateUserState'
    },
    resolve=guess_update_or_create
)


class UpsertUserState(Mutation):
    """
        Abstract base class for mutation
    """
    user_state = Field(UserStateType)

    def mutate(self, info, user_state_data=None):
        """
            Update or create the user state
        :param info:
        :param user_state_data:
        :return:
        """
        update_or_create_values = input_type_parameters_for_update_or_create(user_state_fields, user_state_data)
        # We can do update_or_create since we have a unique user_id in addition to the unique id
        user_state, created = UserState.objects.update_or_create(**update_or_create_values)
        return UpsertUserState(user_state=user_state)


class CreateUserState(UpsertUserState):
    """
        Create UserState mutation class
    """

    class Arguments:
        user_state_data = type('CreateUserStateInputType', (InputObjectType,),
                             input_type_fields(user_state_fields, CREATE, UserStateType))(required=True)


class UpdateUserState(UpsertUserState):
    """
        Update UserState mutation class
    """

    class Arguments:
        user_state_data = type('UpdateUserStateInputType', (InputObjectType,),
                             input_type_fields(user_state_fields, UPDATE, UserStateType))(required=True)


graphql_update_or_create_user_state = graphql_update_or_create(user_state_mutation_config, user_state_fields)
graphql_query_user_states = graphql_query('userStates', user_state_fields)
