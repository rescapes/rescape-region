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
from rescape_graphene import Mutation as UserGroupMutation, Query as UserGroupQuery
from rescape_region.models import Region, UserState, GroupState, Project, Location
from rescape_region.schema_models.group_state_schema import GroupStateType, group_state_fields, CreateGroupState, \
    UpdateGroupState
from rescape_region.schema_models.location_schema import location_fields, LocationType, CreateLocation, UpdateLocation
from rescape_region.schema_models.project_schema import ProjectType, project_fields, CreateProject, UpdateProject
from rescape_region.schema_models.region_schema import RegionType, region_fields, CreateRegion, UpdateRegion
from rescape_region.schema_models.user_state_schema import user_state_fields, UserStateType, CreateUserState, \
    UpdateUserState

logger = logging.getLogger('rescape-region')


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


class UserGroupStateQuery(ObjectType):
    user_states = graphene.List(
        UserStateType,
        **allowed_filter_arguments(user_state_fields, UserStateType)
    )

    group_states = graphene.List(
        GroupStateType,
        **allowed_filter_arguments(group_state_fields, GroupStateType)
    )

    @login_required
    def resolve_user_states(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(UserState, kwargs)

        return UserState.objects.filter(
            **modified_kwargs
        )

    @login_required
    def resolve_group_states(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(GroupState, kwargs)

        return GroupState.objects.filter(
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


class UserGroupStateMutation(graphene.ObjectType):
    create_user_state = CreateUserState.Field()
    update_user_state = UpdateUserState.Field()

    create_group_state = CreateGroupState.Field()
    update_group_state = UpdateGroupState.Field()


def create_schema(user_group=None, user_group_state=None, region=None, project=None, location=None):
    """
        Creates a schema from defaults or allows overrides of any of these schemas
        Each arg if overriden must provide a dict with a query and mutation key, each pointing to the
        override query and mutation graphene.ObjectType
    :param user_group: Handles User and Group queries and mutations (defined in rescape_graphene)
    :param user_group_state: Handles UserState and GroupState queries and mutations. See the default UserState
    and GroupState for an example
    :param region: Handles Region queries and mutations. See the default Region for an example
    :param project: Handles Project queries and mutations. See the default Project for an example
    :param location: Handles Location queries and mutations. See the default Location for an example
    :return:
    """

    obj = R.merge(
        dict(
            user_group=dict(query=UserGroupQuery, mutation=UserGroupMutation),
            user_group_state=dict(query=UserGroupStateQuery, mutation=UserGroupStateMutation),
            region=dict(query=RegionQuery, mutation=RegionMutation),
            project=dict(query=ProjectQuery, mutation=ProjectMutation),
            location=dict(query=LocationQuery, mutation=LocationMutation)
        ),
        # Any non-null arguments take precedence
        R.compact_dict(dict(user_group=user_group, user_group_state=user_group_state, region=region, project=project,
                            location=location))
    )

    class Query(*R.map_with_obj_to_values(lambda k, v: R.prop('query', v), obj)):
        pass

    class Mutation(*R.map_with_obj_to_values(lambda k, v: R.prop('mutation', v), obj)):
        pass

    return Schema(query=Query, mutation=Mutation)


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
