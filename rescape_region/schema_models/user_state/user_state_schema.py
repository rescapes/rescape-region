from json import dumps

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
from rescape_python_helpers import ramda as R, compact

from rescape_region.model_helpers import get_region_model, get_project_model, get_search_location_schema
from rescape_region.models import UserState
from rescape_region.schema_models.user_state.user_state_data_schema import UserStateDataType, user_state_data_fields


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
            q_expressions = process_filter_kwargs(UserState, **R.merge(dict(deleted__isnull=True), kwargs))

            return UserState.objects.filter(
                *q_expressions
            )

    return UserStateQuery


def create_user_state_config(class_config):
    """
        Creates the UserStateType based on specific class_config
    :param class_config: A dict containing class configurations. The default is:
    dict(
        settings=dict(
            model_class=Settings,
            graphene_class=SettingsType,
            graphene_fields=settings_fields,
            query=SettingsQuery,
            mutation=SettingsMutation
        ),
        region=dict(
            model_class=Region,
            graphene_class=RegionType,
            graphene_fields=region_fields,
            query=RegionQuery,
            mutation=RegionMutation
        ),
        project=dict(
            model_class=Project,
            graphene_class=ProjectType,
            graphene_fields=project_fields,
            query=ProjectQuery,
            mutation=ProjectMutation
        ),
        resource=dict(
            model_class=Resource,
            graphene_class=ResourceType,
            graphene_fields=resource_fields,
            query=ResourceQuery,
            mutation=ResourceMutation
        ),
        location=get_location_schema(),
        user_search=get_user_search_data_schema(),
        search_location=get_search_location_schema()
        # additional_user_scope_schemas and additional_user_scopes
        # are passed in from a calling app
        # these are a dict of properties that need to go on user_regions and user_projects
        # at the same level as userSearch. For instance, a user's saved app selections could go here
        # additional_user_scope_schemas = dict(
        # userDesignFeatureLayers=dict(
        #    graphene_class=UserDesignFeatureDataType,
        #    graphene_fields=user_design_feature_data_fields
        # )
        # additional_user_scopes explains the path to Django models within additional_user_scope_schemas
        # additional_django_model_user_scopes = dict(
        # userDesignFeatureLayers=dict(
        #   designFeature=True
        # )
        # Would match the list of some django DesignFeature model instances
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

    additional_django_model_user_scopes = R.prop('additional_django_model_user_scopes', class_config) \
        if R.prop_or(None, 'additional_django_model_user_scopes', class_config) else {}

    # The scope instance types expected in user_state.data
    django_modal_user_state_scopes = [
        # dict(region=True) means search all userRegions for that dict
        dict(pick=dict(userRegions=dict(region=True)), key='region', model=get_region_model()),
        # dict(project=True) means search all userProjects for that dict
        dict(pick=dict(userProjects=dict(project=True)), key='project', model=get_project_model()),
        dict(pick=dict(
            userRegions=[
                dict(
                    userSearch=dict(
                        # dict(searchLocation=True) means search all userSearchLocations for that dict
                        userSearchLocations=dict(searchLocation=True)
                    ),
                    **additional_django_model_user_scopes
                )
            ],
            userProjects=[
                dict(
                    userSearch=dict(
                        # dict(searchLocation=True) means search all userSearchLocations for that dict
                        userSearchLocations=dict(searchLocation=True)
                    ),
                    **additional_django_model_user_scopes
                )
            ]
        ), key='searchLocation', model=get_search_location_schema()['model_class']),
    ]

    @R.curry
    def find_scope_instances_by_id(model, scope_ids):
        return model.objects.all_with_deleted().filter(id__in=scope_ids)

    @R.curry
    def find_scope_instances(new_data, user_state_scope):
        """
            Retrieve the scope instances to verify the Ids
        :param new_data: The data to search
        :param user_state_scope Dict with 'pick' in the shape of the instances we are looking for in new_data,
        e.g. dict(userRegions={region: True}) to search new_data.userRegions[] for all occurrences of {region:...}
         and 'key' which indicates the actually key of the instance (e.g. 'region' for regions)
        :return: dict(ids=The ids found, instances=Instances actually in the database)
        """

        def until(key, value):
            return key != R.prop('key', user_state_scope)

        return R.compose(
            lambda scope_ids: dict(ids=scope_ids, instances=list(
                find_scope_instances_by_id(R.prop('model', user_state_scope), scope_ids))),
            lambda scope_ids: R.unique_by(R.identity, scope_ids),
            lambda scope_objs: compact(R.map(lambda scope_obj: R.prop_or(None, 'id', scope_obj), scope_objs)),
            # Use the pick key property to find the scope instances in the data
            # If we don't match anything we can get null or an empty item. Filter/compact these out
            lambda data: R.filter(
                lambda item: item and (not isinstance(item, list) or R.length(item) != 0),
                list(R.values(R.flatten_dct_until(
                    R.pick_deep(R.prop('pick', user_state_scope), data),
                    until,
                    '.'
                )))
            )
        )(new_data)

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
            validated_scope_instances_and_ids_sets = R.map(find_scope_instances(new_data),
                                                           django_modal_user_state_scopes)
            for i, validated_scope_instances_and_ids in enumerate(validated_scope_instances_and_ids_sets):
                if R.length(validated_scope_instances_and_ids['ids']) != R.length(
                        validated_scope_instances_and_ids['instances']):
                    ids = R.join(', ', validated_scope_instances_and_ids['ids'])
                    instances_string = R.join(', ', R.map(lambda instance: str(instance),
                                                          validated_scope_instances_and_ids['instances']))
                    scope = R.merge(django_modal_user_state_scopes[i],
                                    dict(model=django_modal_user_state_scopes[i]['model'].__name__))
                    raise Exception(
                        f"For scope {dumps(scope)} Some scope ids among ids:[{ids}] being saved in user state do not exist. Found the following instances in the database: {instances_string or 'None'}. UserState.data is {dumps(new_data)}"
                    )

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
                                   input_type_fields(user_state_fields, CREATE, UserStateType)
                                   )(required=True)

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
