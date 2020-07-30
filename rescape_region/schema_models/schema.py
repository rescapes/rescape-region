import logging
import traceback

from graphql import format_error
from rescape_python_helpers import ramda as R

from rescape_graphene import create_schema
from rescape_region.models import Region, Project, Location, Settings
from rescape_region.models.resource import Resource
from rescape_region.schema_models.group_state_schema import create_group_state_query_and_mutation_classes
from rescape_region.schema_models.location_schema import location_fields, LocationType, LocationQuery, LocationMutation
from rescape_region.schema_models.project_schema import ProjectType, project_fields, ProjectQuery, ProjectMutation
from rescape_region.schema_models.region_schema import RegionType, region_fields, RegionQuery, RegionMutation
from rescape_region.schema_models.resource_schema import resource_fields, ResourceType, ResourceQuery, ResourceMutation
from rescape_region.schema_models.settings_schema import SettingsType, settings_fields, SettingsQuery, SettingsMutation
from rescape_region.schema_models.user_state_schema import create_user_state_query_and_mutation_classes

logger = logging.getLogger('rescape_region')

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

def create_default_schema(class_config={}):
    """
        Merges the default graphene types defined in this schema with an application using this library
        that has it's own graphene types. The latter can define overrides for all the default graphene types
        defined in this file. UserState and GroupState are created based on a merger of the types
    :param class_config:
    :return:
    """

    # Merge the incoming class_config with our defaults
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
    return create_schema(query_and_mutation_class_lookups)


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
