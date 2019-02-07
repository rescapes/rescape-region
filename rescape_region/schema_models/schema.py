import graphene
import logging
import sys
import traceback

from graphql import format_error
from rescape_graphene.graphql_helpers.schema_helpers import allowed_filter_arguments, \
    process_filter_kwargs
from rescape_python_helpers import ramda as R
from graphene import ObjectType, Schema
from graphql_jwt.decorators import login_required
from rescape_graphene import Mutation as GrapheneMutation, Query as GrapheneQuery
from rescape_region.models import Region, UserState, GroupState, Project, Location
from rescape_region.schema_models.group_state_schema import create_group_state_config
from rescape_region.schema_models.location_schema import location_fields, LocationType, CreateLocation, UpdateLocation
from rescape_region.schema_models.project_schema import ProjectType, project_fields, CreateProject, UpdateProject
from rescape_region.schema_models.region_schema import RegionType, region_fields, CreateRegion, UpdateRegion
from rescape_region.schema_models.user_state_schema import create_user_state_schema

logger = logging.getLogger('rescape-region')

# We construct the Graphene GroupState class using the Region defined in this package
group_state_schema = create_group_state_config(dict(
    region=dict(
        model_class=Region,
        graphene_class=RegionType,
        fields=region_fields
    )
))

# We construct the Graphene GroupState class using the Region and Project defined in this package
user_state_schema = create_user_state_schema(dict(
    region=dict(
        model_class=Region,
        graphene_class=RegionType,
        fields=region_fields
    ),
    project=dict(
        model_class=Project,
        graphene_class=ProjectType,
        fields=project_fields
    ),
    location=dict(
        model_class=Location,
        graphene_class=LocationType,
        fields=location_fields
    )
))


class RegionQuery(ObjectType):
    regions = graphene.List(
        RegionType,
        **allowed_filter_arguments(region_fields, RegionType)
    )

    @login_required
    def resolve_regions(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(Region, kwargs)

        return Region.objects.filter(
            **modified_kwargs
        )


class ProjectQuery(ObjectType):
    projects = graphene.List(
        ProjectType,
        **allowed_filter_arguments(project_fields, ProjectType)
    )

    @login_required
    def resolve_projects(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(Project, kwargs)
        return Project.objects.filter(
            **modified_kwargs
        )


class LocationQuery(ObjectType):
    locations = graphene.List(
        LocationType,
        **allowed_filter_arguments(location_fields, LocationType)
    )

    @login_required
    def resolve_locations(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(Location, kwargs)

        return Location.objects.filter(
            **modified_kwargs
        )


class UserStateQuery(ObjectType):
    user_states = graphene.List(
        R.prop('graphene_class', user_state_schema),
        **allowed_filter_arguments(R.prop('fields', user_state_schema), R.prop('graphene_class', user_state_schema))
    )

    @login_required
    def resolve_user_states(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(UserState, kwargs)

        return UserState.objects.filter(
            **modified_kwargs
        )


class GroupStateQuery(ObjectType):
    group_states = graphene.List(
        R.prop('graphene_class', group_state_schema),
        **allowed_filter_arguments(R.prop('fields', group_state_schema), R.prop('graphene_class', group_state_schema))
    )

    @login_required
    def resolve_group_states(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(GroupState, kwargs)

        return R.prop('model_class', group_state_schema).objects.filter(
            **modified_kwargs
        )


class RegionMutation(graphene.ObjectType):
    create_region = CreateRegion.Field()
    update_region = UpdateRegion.Field()


class ProjectMutation(graphene.ObjectType):
    create_project = CreateProject.Field()
    update_project = UpdateProject.Field()


class LocationMutation(graphene.ObjectType):
    create_location = CreateLocation.Field()
    update_location = UpdateLocation.Field()


class UserStateMutation(graphene.ObjectType):
    create_group_state = R.prop('create_mutation_class', group_state_schema).Field()
    update_group_state = R.prop('update_mutation_class', group_state_schema).Field()


class GroupStateMutation(graphene.ObjectType):
    create_user_state = R.prop('create_mutation_class', user_state_schema).Field()
    update_user_state = R.prop('update_mutation_class', user_state_schema).Field()


def create_query_and_mutation_classes(user=None, user_state=None, group_state=None, region=None, project=None,
                                      location=None):
    """
        Creates a Query class and Mutation classs from defaults or allows overrides of any of these schemas
        Each arg if overriden must provide a dict with a query and mutation key, each pointing to the
        override query and mutation graphene.ObjectType
    :param user: Handles User and Group queries and mutations (defined in rescape_graphene)
    :param user_state: Handles UserState queries and mutations. See the default UserState for an example
    :param group_state: Handles GroupState queries and mutations. See the default GroupState for an example
    :param region: Handles Region queries and mutations. See the default Region for an example
    :param project: Handles Project queries and mutations. See the default Project for an example
    :param location: Handles Location queries and mutations. See the default Location for an example
    :return: A dict with query and mutation for the two dynamic classes
    """
    obj = R.merge(
        dict(
            user=dict(query=GrapheneQuery, mutation=GrapheneMutation),
            user_state=dict(query=UserStateQuery, mutation=UserStateMutation),
            group_state=dict(query=GroupStateQuery, mutation=GroupStateMutation),
            region=dict(query=RegionQuery, mutation=RegionMutation),
            project=dict(query=ProjectQuery, mutation=ProjectMutation),
            location=dict(query=LocationQuery, mutation=LocationMutation)
        ),
        # Any non-null arguments take precedence
        R.compact_dict(dict(
            user=user,
            user_state=user_state,
            group_state=group_state,
            region=region,
            project=project,
            location=location)
        )
    )

    class Query(*R.map_with_obj_to_values(lambda k, v: R.prop('query', v), obj)):
        pass

    class Mutation(*R.map_with_obj_to_values(lambda k, v: R.prop('mutation', v), obj)):
        pass

    return dict(query=Query, mutation=Mutation)


def create_query_mutation_schema(user_group=None, user_group_state=None, region=None, project=None, location=None):
    """
        Creates a schema from defaults or allows overrides of any of these schemas
        Each arg if overridden must provide a dict with a query and mutation key, each pointing to the
        override query and mutation graphene.ObjectType
    :param user_group: Handles User and Group queries and mutations (defined in rescape_graphene)
    :param user_group_state: Handles UserState and GroupState queries and mutations. See the default UserState
    and GroupState for an example
    :param region: Handles Region queries and mutations. See the default Region for an example
    :param project: Handles Project queries and mutations. See the default Project for an example
    :param location: Handles Location queries and mutations. See the default Location for an example
    :return:
    """

    obj = create_query_and_mutation_classes(user_group, user_group_state, region, project, location)
    schema = Schema(query=R.prop('query', obj), mutation=R.prop('mutation', obj))
    return dict(query=R.prop('query', obj), mutation=R.prop('mutation', obj), schema=schema)


def create_schema(user_group=None, user_group_state=None, region=None, project=None, location=None):
    return R.prop('schema', create_query_mutation_schema(user_group, user_group_state, region, project, location))


schema = create_schema()


def dump_errors(result):
    """
        Dump any errors to in the result to stderr
    :param result:
    :return:
    """
    if R.has('errors', result):
        for error in result['errors']:
            logger.error(format_error(error))
            if 'stack' in error:
                traceback.print_tb(error['stack'], limit=10, file=sys.stderr)
