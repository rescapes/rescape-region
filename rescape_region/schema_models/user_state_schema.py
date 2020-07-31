import graphene
from graphene import Field, Mutation, InputObjectType, ObjectType
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import input_type_fields, REQUIRE, DENY, CREATE, \
    input_type_parameters_for_update_or_create, UPDATE, \
    guess_update_or_create, graphql_update_or_create, graphql_query, merge_with_django_properties, UserType, \
    enforce_unique_props, resolver_for_dict_field, user_fields
from rescape_graphene.graphql_helpers.schema_helpers import merge_data_fields_on_update, update_or_create_with_revision, \
    top_level_allowed_filter_arguments, process_filter_kwargs
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_python_helpers import ramda as R

from rescape_region.model_helpers import get_region_model, get_project_model
from rescape_region.models import UserState
from rescape_region.schema_models.user_state_data_schema import UserStateDataType, user_state_data_fields


def create_user_state_query_and_mutation_classes(class_config):
    user_state_config = create_user_state_config(class_config)
    return dict(
        query=create_user_state_query(user_state_config),
        mutation=create_user_state_mutation(user_state_config)
    )


def create_user_state_mutation(user_state_config):
    class UserStateMutation(graphene.ObjectType):
        create_user_state = R.prop('create_mutation_class', user_state_config).Field()
        update_user_state = R.prop('update_mutation_class', user_state_config).Field()

    return UserStateMutation


def create_user_state_query(user_state_config):
    class UserStateQuery(ObjectType):
        user_states = graphene.List(
            R.prop('graphene_class', user_state_config),
            **top_level_allowed_filter_arguments(R.prop('graphene_fields', user_state_config),
                                                 R.prop('graphene_class', user_state_config))
        )

        @login_required
        def resolve_user_states(self, info, **kwargs):
            q_expressions = process_filter_kwargs(UserState, **kwargs)

            return UserState.objects.filter(
                *q_expressions
            )

    return UserStateQuery


def create_user_state_config(class_config):
    """
        Creates the UserStateType based on specific class_config
    :param class_config: A dict containing class configurations. Right now it's only region in the form
    dict(
        region=dict(
            model_class=...,
            graphene_class=...,
            fields=...
        )
        project=dict(
            model_class=...,
            graphene_class=...,
            fields=...
        ),
        location=dict(
            model_class=...,
            graphene_class=...,
            fields=...
        )
    )
    :return:
    """

    class UserStateType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
        """
            UserStateType models UserState, which represents the settings both imposed upon and chosen by the user
        """
        id = graphene.Int(source='pk')

        class Meta:
            model = UserState

    # Modify data field to use the resolver.
    # I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
    # Django model to generate the fields
    UserStateType._meta.fields['data'] = Field(
        UserStateDataType(class_config),
        resolver=resolver_for_dict_field
    )

    user_state_fields = merge_with_django_properties(UserStateType, dict(
        id=dict(create=DENY, update=REQUIRE),
        # This is a Foreign Key. Graphene generates these relationships for us, but we need it here to
        # support our Mutation subclasses and query_argument generation
        # For simplicity we limit fields to id. Mutations can only use id, and a query doesn't need other
        # details of the User--it can query separately for that
        user=dict(graphene_type=UserType, fields=user_fields),
        # This refers to the UserState, which is a representation of all the json fields of UserState.data
        data=dict(graphene_type=UserStateDataType(class_config), fields=user_state_data_fields(class_config),
                  default=lambda: dict()),
        **reversion_and_safe_delete_types
    ))

    user_state_mutation_config = dict(
        class_name='UserState',
        crud={
            CREATE: 'createUserState',
            UPDATE: 'updateUserState'
        },
        resolve=guess_update_or_create
    )

    # The scope instance types expected in user_state.data
    user_state_scopes = [
        dict(prop='userRegions', scope_instance_path='region', model=get_region_model()),
        dict(prop='userProjects', scope_instance_path='project', model=get_project_model())
    ]

    @R.curry
    def find_scope_instance(model, scope_id):
        return model.objects.all_with_deleted().filter(id=scope_id).values('id', 'name')

    @R.curry
    def find_scope_instances(new_data, user_state_scope):
        """
            Retrieve the scope instances to verify the Ids
        :param new_data:
        :param path:
        :param model:
        :return:
        """
        user_scope_instances = R.prop_or([], R.prop('prop', user_state_scope), new_data)
        return R.map(
            lambda user_scope_instance: find_scope_instance(
                R.prop('model', user_state_scope),
                R.item_path(
                    [R.prop('scope_instance_path', user_state_scope), 'id'],
                    user_scope_instance)
            ),
            user_scope_instances
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

            # Check that all the scope instances in user_state.data exist. We permit deleted instances for now.
            new_data = R.prop_or({}, 'data', user_state_data)
            # If any scope instances specified in new_data don't exist, throw an error
            validated_scope_instances = R.chain(find_scope_instances(new_data), user_state_scopes)
            if R.any_satisfy(lambda query: not R.equals(1, query.count()), validated_scope_instances):
                raise Exception(
                    f"Some scope instances being saved in user_state do not exist. Found the following: {validated_scope_instances}. UserState.data is {new_data}")

            # id or user.id can be used to identify the existing instance
            id_props = R.compact_dict(
                dict(
                    id=R.prop_or(None, 'id', user_state_data),
                    user_id=R.item_str_path_or(None, 'user.id', user_state_data)
                )
            )

            def fetch_and_merge(user_state_data, props):
                existing = UserState.objects.filter(**props)
                # If the user doesn't have a user state yet
                if not R.length(existing):
                    return user_state_data

                return merge_data_fields_on_update(
                    ['data'],
                    R.head(existing),
                    # Merge existing's id in case it wasn't in user_state_data
                    R.merge(user_state_data, R.pick(['id'], existing))
                )

            modified_data = R.if_else(
                R.compose(R.length, R.keys),
                lambda props: fetch_and_merge(user_state_data, props),
                lambda x: user_state_data
            )(id_props)

            update_or_create_values = input_type_parameters_for_update_or_create(
                user_state_fields,
                # Make sure that all props are unique that must be, either by modifying values or erring.
                enforce_unique_props(
                    user_state_fields,
                    modified_data)
            )

            user_state, created = update_or_create_with_revision(UserState, update_or_create_values)
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
    graphql_query_user_states = graphql_query(UserStateType, user_state_fields, 'userStates')

    return dict(
        model_class=UserState,
        graphene_class=UserStateType,
        graphene_fields=user_state_fields,
        create_mutation_class=CreateUserState,
        update_mutation_class=UpdateUserState,
        graphql_mutation=graphql_update_or_create_user_state,
        graphql_query=graphql_query_user_states
    )
