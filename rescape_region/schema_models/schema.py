import logging
import traceback

import graphene
from graphene import ObjectType, Schema
from graphql import format_error
from graphql_jwt.decorators import login_required
from rescape_graphene import Mutation as GrapheneMutation, Query as GrapheneQuery
from rescape_graphene.graphql_helpers.schema_helpers import allowed_filter_arguments, \
    process_filter_kwargs
from rescape_python_helpers import ramda as R

from rescape_region.models import Region, UserState, GroupState, Project, Location, Settings
from rescape_region.models.resource import Resource
from rescape_region.schema_models.group_state_schema import create_group_state_config
from rescape_region.schema_models.location_schema import location_fields, LocationType, LocationQuery, LocationMutation
from rescape_region.schema_models.project_schema import ProjectType, project_fields, ProjectQuery, ProjectMutation
from rescape_region.schema_models.region_schema import RegionType, region_fields, RegionQuery, RegionMutation
from rescape_region.schema_models.resource_schema import resource_fields, ResourceType, ResourceQuery, ResourceMutation
from rescape_region.schema_models.settings_schema import SettingsType, settings_fields, SettingsQuery, SettingsMutation
from rescape_region.schema_models.user_state_schema import create_user_state_config

logger = logging.getLogger('rescape_region')

def create_user_state_query(user_state_config):
    class UserStateQuery(ObjectType):
        user_states = graphene.List(
            R.prop('graphene_class', user_state_config),
            **allowed_filter_arguments(R.prop('graphene_fields', user_state_config), R.prop('graphene_class', user_state_config))
        )

        @login_required
        def resolve_user_states(self, info, **kwargs):
            q_expressions = process_filter_kwargs(UserState, kwargs)

            return UserState.objects.filter(
                *q_expressions
            )

    return UserStateQuery


def create_user_state_query_and_mutation_classes(class_config):
    user_state_config = create_user_state_config(class_config)
    return dict(
        query=create_user_state_query(user_state_config),
        mutation=create_user_state_mutation(user_state_config)
    )


def create_group_state_query(group_state_config):
    class GroupStateQuery(ObjectType):
        group_states = graphene.List(
            R.prop('graphene_class', group_state_config),
            **allowed_filter_arguments(R.prop('graphene_fields', group_state_config),
                                       R.prop('graphene_class', group_state_config))
        )

        @login_required
        def resolve_group_states(self, info, **kwargs):
            q_expressions = process_filter_kwargs(GroupState, kwargs)

            return R.prop('model_class', group_state_config).objects.filter(
                *q_expressions
            )

    return GroupStateQuery


def create_group_state_query_and_mutation_classes(class_config):
    group_state_config = create_group_state_config(class_config)
    return dict(
        query=create_group_state_query(group_state_config),
        mutation=create_group_state_mutation(group_state_config)
    )

def create_user_state_mutation(user_state_config):
    class UserStateMutation(graphene.ObjectType):
        create_user_state = R.prop('create_mutation_class', user_state_config).Field()
        update_user_state = R.prop('update_mutation_class', user_state_config).Field()

    return UserStateMutation


def create_group_state_mutation(group_state_config):
    class GroupStateMutation(graphene.ObjectType):
        create_user_state = R.prop('create_mutation_class', group_state_config).Field()
        update_user_state = R.prop('update_mutation_class', group_state_config).Field()

    return GroupStateMutation


default_class_config = dict(
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
    location=dict(
        model_class=Location,
        graphene_class=LocationType,
        graphene_fields=location_fields,
        query=LocationQuery,
        mutation=LocationMutation
    )
)


def create_query_and_mutation_classes(class_config):
    """
        Creates a Query class and Mutation classs from defaults or allows overrides of any of these schemas
        Each arg if overriden must provide a dict with a query and mutation key, each pointing to the
        override query and mutation graphene.ObjectType
    :param class_config: Handles User and Group queries and mutations (defined in rescape_graphene)
    :param class_config.region: Handles Region queries and mutations. See the default Region for an example
    :param class_config.project: Handles Project queries and mutations. See the default Project for an example
    :param class_config.location: Handles Location queries and mutations. See the default Location for an example
    :return: A dict with query and mutation for the two dynamic classes
    """

    merged_class_config = R.merge(
        default_class_config,
        class_config
    )
    # We use region, project, and location to create user_state and group_state
    # This is because user_state and group_state store settings for a user or group about those enties
    # For instance, what regions does a group have access to or what location is selected by a user
    user_state = create_user_state_query_and_mutation_classes(merged_class_config)
    group_state = create_group_state_query_and_mutation_classes(merged_class_config)

    query_and_mutation_class_lookups = R.merge(
        merged_class_config,
        dict(
            user_state=user_state,
            group_state=group_state
        )
    )

    class Query(
        GrapheneQuery,
        *R.map_with_obj_to_values(
            lambda k, v: R.prop('query', v), query_and_mutation_class_lookups
        )
    ):
        pass

    class Mutation(
        GrapheneMutation,
        *R.map_with_obj_to_values(
            lambda k, v: R.prop('mutation', v), query_and_mutation_class_lookups
        )
    ):
        pass

    return dict(query=Query, mutation=Mutation)


def create_query_mutation_schema(class_config):
    """
        Creates a schema from defaults or allows overrides of any of these schemas
        Each arg if overridden must provide a dict with a query and mutation key, each pointing to the
        override query and mutation graphene.ObjectType
        :param class_config
        :param class_config.user_group: Handles User and Group queries and mutations (defined in rescape_graphene)
        :param class_config.user_group_state: Handles UserState and GroupState queries and mutations. See the default UserState
        and GroupState for an example
        :param class_config.region: Handles Region queries and mutations. See the default Region for an example
        :param class_config.project: Handles Project queries and mutations. See the default Project for an example
        :param class_config.location: Handles Location queries and mutations. See the default Location for an example
        :return:
    """

    obj = create_query_and_mutation_classes(class_config)
    schema = Schema(query=R.prop('query', obj), mutation=R.prop('mutation', obj))
    return dict(query=R.prop('query', obj), mutation=R.prop('mutation', obj), schema=schema)


def create_schema(class_config={}):
    return R.prop('schema', create_query_mutation_schema(class_config))


def dump_errors(result):
    """
        Dump any errors to in the result to stderr
    :param result:
    :return:
    """
    if R.has('errors', result):
        for error in result['errors']:
            logging.exception(traceback)
            if hasattr(error, 'stack'):
                # Syncrounous calls or something
                # See https://github.com/graphql-python/graphql-core/issues/237
                tb = error['stack']
            else:
                # Promises
                tb = error.__traceback__
            formatted_tb = traceback.format_tb(tb)
            error.stack = error.__traceback__
            # This hopefully includes the traceback
            logger.exception(format_error(error))
