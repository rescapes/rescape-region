import copy
from collections import namedtuple
from json import dumps

from deepmerge import Merger
from deepmerge.strategy.list import ListStrategies
from deepmerge.strategy.dict import DictStrategies
from deepmerge.strategy.fallback import FallbackStrategies
from deepmerge.strategy.type_conflict import TypeConflictStrategies

import graphene
from django.utils.timezone import now
from graphene import Field, Mutation, InputObjectType, ObjectType
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import input_type_fields, REQUIRE, DENY, CREATE, \
    input_type_parameters_for_update_or_create, UPDATE, \
    guess_update_or_create, graphql_update_or_create, graphql_query, merge_with_django_properties, UserType, \
    enforce_unique_props, resolver_for_dict_field, user_fields
from rescape_graphene.graphql_helpers.schema_helpers import merge_data_fields_on_update, update_or_create_with_revision, \
    top_level_allowed_filter_arguments, process_filter_kwargs, ALLOW
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_python_helpers import ramda as R, compact

from rescape_region.model_helpers import get_region_model, get_project_model, get_search_location_schema
from rescape_region.models import UserState
from rescape_region.schema_models.user_state.user_state_data_schema import UserStateDataType, user_state_data_fields
from rescape_graphene.graphql_helpers.json_field_helpers import resolve_selections, pick_selections


class MyListStrategies(ListStrategies):
    @staticmethod
    def strategy_override_non_null(config, path, base, nxt):
        """ use the list nxt. """
        return nxt if nxt else base


class MyMerger(Merger):
    PROVIDED_TYPE_STRATEGIES = {
        list: MyListStrategies,
        dict: DictStrategies
    }
    # def __init__(self,
    #              type_strategies,
    #              fallback_strategies,
    #              type_conflict_strategies):
    #     self._fallback_strategy = FallbackStrategies(fallback_strategies)
    #
    #     expanded_type_strategies = []
    #     for typ, strategy in type_strategies:
    #         if typ in self.PROVIDED_TYPE_STRATEGIES:
    #             strategy = self.PROVIDED_TYPE_STRATEGIES[typ](strategy)
    #         expanded_type_strategies.append((typ, strategy))
    #     self._type_strategies = expanded_type_strategies
    #
    #     self._type_conflict_strategy = TypeConflictStrategies(
    #         type_conflict_strategies
    #     )


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


def resolver_for_data_field(resource, context, **kwargs):
    """
        Like resolver_for_dict_field, but default the data property to {userRegions:[], userProjects:[]}
        in case a mutation messes it up (This should be a temporary problem until we fix the mutation).
    :param resource:
    :param context:
    :params kwargs: Arguments to filter with
    :return:
    """
    selections = resolve_selections(context)
    field_name = context.field_name
    data = getattr(resource, field_name) if (hasattr(resource, field_name) and R.prop(field_name, resource)) else {}
    data['userRegions'] = R.prop_or([], 'userRegions', data)
    data['userProjects'] = R.prop_or([], 'userProjects', data)

    # We only let this value through if it matches the kwargs
    # TODO data doesn't include full values for embedded model values, rather just {id: ...}. So if kwargs have
    # searches on other values of the model this will fail. The solution is to load the model values, but I
    # need some way to figure out where they are in data
    passes = R.dict_matches_params_deep(kwargs, data)
    # Pick the selections from our resource json field value default to {} if resource[field_name] is null
    return pick_selections(selections, data) if passes else namedtuple('DataTuple', [])()


scope_key_lookup = dict(userProjects='project', userRegions='region')


def user_scope_instances_by_id(user_scope_key, user_state_data):
    # Resolve the user scope instances
    return R.from_pairs(
        R.map(
            lambda user_scope: [
                R.item_path_or(None, [scope_key_lookup[user_scope_key], 'id'], user_scope),
                user_scope
            ],
            R.prop_or([], user_scope_key, user_state_data)
        )
    )


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
        resolver=resolver_for_data_field
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
    additional_user_scope_schemas = R.prop('additional_user_scope_schemas', class_config) \
        if R.prop_or(None, 'additional_user_scope_schemas', class_config) else {}

    # The scope instance types expected in user_state.data
    django_modal_user_state_scopes = R.concat([
        # dict(region=True) means search all userRegions for that dict
        dict(pick=dict(userRegions=dict(region=True)), key='region', model=get_region_model()),
        # dict(project=True) means search all userProjects for that dict
        dict(pick=dict(userProjects=dict(project=True)), key='project', model=get_project_model()),
        dict(
            pick=dict(
                userRegions=[
                    dict(
                        userSearch=dict(
                            # dict(searchLocation=True) means search all userSearchLocations for that dict
                            userSearchLocations=dict(
                                searchLocation=True,
                            )
                        )
                    )
                ],
                userProjects=[
                    dict(
                        userSearch=dict(
                            # dict(searchLocation=True) means search all userSearchLocations for that dict
                            userSearchLocations=dict(searchLocation=True)
                        )
                    )
                ]
            ),
            key='searchLocation',
            model=get_search_location_schema()['model_class'],
            # These can be modified when userState is mutated
            can_mutate_related=True
        ),
    ],
        # Map each additional_django_model_user_scopes to a scope config
        R.map_with_obj_to_values(
            lambda field_name, additional_django_model_user_scope: dict(
                pick=dict(
                    userRegions=[
                        {field_name: additional_django_model_user_scope}
                    ],
                    userProjects=[
                        {field_name: additional_django_model_user_scope}
                    ]
                ),
                # Assume the scope object is the deepest field
                key=list(R.keys(R.flatten_dct(additional_django_model_user_scope, '.')))[0].split('.')[-1],
                # model isn't needed unless can_mutate_related is true
                model=additional_user_scope_schemas[field_name]['model'],
                # These can be modified when userState is mutated
                can_mutate_related=R.prop_or(False, 'can_mutate_related', additional_django_model_user_scope)
            ),
            additional_django_model_user_scopes
        )
    )

    @R.curry
    def find_scope_instances_by_id(model, scope_ids):
        return model.objects.all_with_deleted().filter(id__in=scope_ids)

    @R.curry
    def find_scope_instances(new_data, user_state_scope):
        """
            Retrieve the scope instances to verify the Ids.
            Scope instances must have ids unless they are allowed to be created/updated
            during the userState mutation (such as searchLocations)
        :param new_data: The data to search
        :param user_state_scope Dict with 'pick' in the shape of the instances we are looking for in new_data,
        e.g. dict(userRegions={region: True}) to search new_data.userRegions[] for all occurrences of {region:...}
         and 'key' which indicates the actually key of the instance (e.g. 'region' for regions)
        :return: dict(
            instances=Instances actually in the database,
        )
        """

        def until(key, value):
            return key != R.prop('key', user_state_scope)

        return R.compose(
            lambda scope_dict: dict(
                # See which instances with ids are actually in the database
                # If any are missing we have an invalid update
                instances=list(
                    find_scope_instances_by_id(R.prop('model', user_state_scope), scope_dict['scope_ids'])
                ),
                # The path from userRegions or userProjects to the scope instances, used to replace
                # a null update value with the existing values
                user_scope_path=list(R.keys(R.flatten_dct(user_state_scope, '.')))[0],
                **scope_dict
            ),
            lambda scope_objs: dict(
                # Unique by id or accept if there is no id, this loses data, but it's just for validation
                scope_objs=R.unique_by(lambda obj: R.prop_or(str(now()), 'id', obj['value']), scope_objs),
                scope_ids=R.unique_by(
                    R.identity,
                    compact(
                        R.map(
                            lambda scope_obj: R.prop_or(None, 'id', scope_obj['value']), scope_objs
                        )
                    )
                )
            ),
            # Use the pick key property to find the scope instances in the data
            # If we don't match anything we can get null or an empty item. Filter/compact these out
            R.filter(
                lambda obj: obj['value'] and (not isinstance(obj['value'], list) or R.length(obj['value']) != 0)
            ),
            R.map(
                lambda pair: dict(key=pair[0], value=pair[1])
            ),
            lambda flattened_data: R.to_pairs(flattened_data),
            lambda data: R.flatten_dct_until(
                R.pick_deep_all_array_items(R.prop('pick', user_state_scope), data),
                until,
                '.'
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
            new_data = R.prop_or({},     'data', user_state_data)
            updated_new_data = copy.deepcopy(new_data)
            old_user_state_data = UserState.objects.get(id=user_state_data['id']).data if R.prop_or(None, 'id', user_state_data) else None

            # If any scope instances specified in new_data don't exist, throw an error
            validated_scope_objs_instances_and_ids_sets = R.map(
                find_scope_instances(updated_new_data),
                django_modal_user_state_scopes
            )
            for i, validated_scope_objs_instances_and_ids in enumerate(validated_scope_objs_instances_and_ids_sets):
                scope = R.merge(
                    django_modal_user_state_scopes[i],
                    dict(model=django_modal_user_state_scopes[i]['model'].__name__)
                )

                if R.length(validated_scope_objs_instances_and_ids['scope_ids']) != R.length(
                        validated_scope_objs_instances_and_ids['instances']):
                    ids = R.join(', ', validated_scope_objs_instances_and_ids['scope_ids'])
                    instances_string = R.join(', ', R.map(lambda instance: str(instance),
                                                          validated_scope_objs_instances_and_ids['instances']))
                    raise Exception(
                        f"For scope {dumps(scope)} Some scope ids among ids:[{ids}] being saved in user state do not exist. Found the following instances in the database: {instances_string or 'None'}. UserState.data is {dumps(updated_new_data)}"
                    )

                model = django_modal_user_state_scopes[i]['model']
                updated_new_data = handle_can_mutate_related(
                    model,
                    scope,
                    updated_new_data,
                    validated_scope_objs_instances_and_ids
                )

            # If either userProjects or userRegions are null, it means those scope instances aren't part
            # of the update, so merge in the old values
            if R.prop_or(None, 'id', user_state_data) and R.any_satisfy(
                    lambda user_scope_key: not R.prop_or(None, user_scope_key, updated_new_data),
                    ['userProjects', 'userRegions']
            ):
                # The special update case where one userScope collection is null,
                # indicates that we are only updating one userScope object. The rest
                # should remain the same and not be removed
                for user_scope_key in ['userProjects', 'userRegions']:
                    # Database values
                    old_user_scopes_by_id = user_scope_instances_by_id(
                        user_scope_key,
                        old_user_state_data
                    )
                    # New values with updates applied
                    new_user_scopes_by_id = user_scope_instances_by_id(
                        user_scope_key,
                        updated_new_data
                    )
                    # Prefer the old over the new, merging all objects but overriding lists
                    # We override lists because a non-null list always replaces the old list in the database
                    updated_new_data[user_scope_key] = R.values(R.merge_deep(
                        old_user_scopes_by_id,
                        new_user_scopes_by_id,
                        MyMerger(
                            # pass in a list of tuples,with the
                            # strategies you are looking to apply
                            # to each type.
                            [
                                (list, ["override_non_null"]),
                                (dict, ["merge"])
                            ],
                            # next, choose the fallback strategies,
                            # applied to all other types:
                            ["override"],
                            # finally, choose the strategies in
                            # the case where the types conflict:
                            ["override"]
                        )
                    ))

            # Update user_state_data the updated data
            modified_user_state_data = R.merge(user_state_data, dict(data=updated_new_data))

            # id or user.id can be used to identify the existing instance
            id_props = R.compact_dict(
                dict(
                    id=R.prop_or(None, 'id', modified_user_state_data),
                    user_id=R.item_str_path_or(None, 'user.id', modified_user_state_data)
                )
            )

            def fetch_and_merge(modified_user_state_data, props):
                existing = UserState.objects.filter(**props)
                # If the user doesn't have a user state yet
                if not R.length(existing):
                    return modified_user_state_data

                return merge_data_fields_on_update(
                    ['data'],
                    R.head(existing),
                    # Merge existing's id in case it wasn't in user_state_data
                    R.merge(modified_user_state_data, R.pick(['id'], existing))
                )

            modified_data = R.if_else(
                R.compose(R.length, R.keys),
                lambda props: fetch_and_merge(modified_user_state_data, props),
                lambda _: modified_user_state_data
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


def handle_can_mutate_related(model, scope, updated_new_data, validated_scope_objs_instances_and_ids):
    # This indicates that scope_objs were submitted that didn't have ids
    # This is allowed if those scope_objs can be created/updated when the userState is mutated
    if R.prop_or(False, 'can_mutate_related', scope):
        for scope_obj_key_value in validated_scope_objs_instances_and_ids['scope_objs']:

            def omit_to_many(scope_obj):
                return R.omit(R.map(R.prop('attname'), model._meta.many_to_many), scope_obj)

            scope_obj = scope_obj_key_value['value']
            scope_obj_path = scope_obj_key_value['key']
            if R.length(R.keys(R.omit(['id'], scope_obj))):
                if R.prop_or(False, 'id', scope_obj):
                    # Update, we don't need the result since it's already in user_state.data
                    instance, created = model.objects.update_or_create(
                        defaults=R.omit(['id'], omit_to_many(scope_obj)),
                        **R.pick(['id'], scope_obj)
                    )
                else:
                    # Create
                    instance = model(**omit_to_many(scope_obj))
                    instance.save()
                    # We need to replace the object
                    # passed in with an object containing the id of the instance
                    updated_new_data = R.fake_lens_path_set(
                        scope_obj_path.split('.'),
                        R.pick(['id'], instance),
                        updated_new_data
                    )
            for to_many in model._meta.many_to_many:
                if to_many.attname in R.keys(scope_obj):
                    # Set existing related values to the created/updated instances
                    getattr(instance, to_many.attname).set(R.map(R.prop('id'), scope_obj[to_many.attname]))
    return updated_new_data
