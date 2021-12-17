import json
import logging
import traceback

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet
from django.db.models.base import Model
from graphene.types.base import BaseType
from graphene.types.mutation import MutationOptions
from graphene_django.types import ErrorType
from graphql import format_error
from rescape_graphene import create_schema
from rescape_python_helpers import ramda as R

from rescape_region.schema_models.scope.project.project_schema import ProjectType, project_fields, ProjectQuery, \
    ProjectMutation
from rescape_region.schema_models.user_state.group_state_schema import create_group_state_query_and_mutation_classes
from rescape_region.schema_models.user_state.user_state_schema import create_user_state_query_and_mutation_classes

logger = logging.getLogger('rescape_graphene')


def default_class_config():
    # Import here to prevent circular dependencies
    from rescape_region.model_helpers import get_user_search_data_schema, get_location_schema, \
        get_search_location_schema
    from rescape_region.models import Region, Project, Settings
    from rescape_region.models.resource import Resource
    from rescape_region.schema_models.scope.region.region_schema import RegionType, region_fields, RegionQuery, \
        RegionMutation
    from rescape_region.schema_models.resource.resource_schema import resource_fields, ResourceType, ResourceQuery, \
        ResourceMutation
    from rescape_region.schema_models.settings.settings_schema import SettingsType, settings_fields, SettingsQuery, \
        SettingsMutation

    return dict(
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
        default_class_config(),
        class_config
    )

    # We use region, project, and location to create user_state and group_state
    # This is because user_state and group_state store settings for a user or group about those enties
    # For instance, what regions does a group have access to or what location is selected by a user
    user_state = create_user_state_query_and_mutation_classes(merged_class_config)
    group_state = create_group_state_query_and_mutation_classes(merged_class_config)

    # Note that user_search is a data class, not a model class, so isn't queried/mutated directly, but via user_state
    # additional_user_scope_schemas and additional_django_model_user_scopes are used for configured
    # UserStateSchema
    query_and_mutation_class_lookups = R.merge(
        R.omit(['user_search', 'additional_user_scope_schemas', 'additional_django_model_user_scopes'],
               merged_class_config),
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


class MyDjangoJSONEncoder(DjangoJSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, (Model, BaseType)):
            return o.__dict__
        else:
            return super().default(o)


# https://stackoverflow.com/questions/52711580/how-to-see-graphene-django-debug-logs
def log_request_body(info, response_or_error):
    body = info.context._body.decode('utf-8')
    try:
        json_body = json.loads(body)
        (logger.error if isinstance(response_or_error, ErrorType) else logger.debug)(
            f" User: {info.context.user} \n Action: {json_body['operationName']} \n Variables: {json_body['variables']} \n Body:  {json_body['query']}",
        )
        if hasattr(response_or_error, '_meta') and isinstance(response_or_error._meta, MutationOptions):
            # Just log top level types
            if isinstance(response_or_error, (Model)):
                mutation_response = json.dumps(
                    R.omit(['_state'], response_or_error.__dict__),
                    sort_keys=True,
                    indent=1,
                    cls=MyDjangoJSONEncoder
                )
                logger.debug(f'Mutation returned {mutation_response}')
            elif isinstance(response_or_error, (BaseType)):
                try:
                    mutation_response = json.dumps(
                        R.omit(['_state'], response_or_error.__dict__),
                        sort_keys=True,
                        indent=1,
                    )
                    logger.debug(f'Mutation returned {mutation_response}')
                except:
                    logger.debug(f'Mutation returned {response_or_error.__class__}')
        else:
            if hasattr(response_or_error, 'objects'):
                count = response_or_error.objects.count()
                # Log up to 100 ids, don't log if it's a larger set because it might be a paging query
                ids = R.join(' ',
                             ['', 'having ids:',
                              R.join(', ', R.map(R.prop("id"), response_or_error.objects.values('id')))]) if count < 100 else ""
                logger.debug(f'Paginated Query Page {response_or_error.page} of page size {response_or_error.page_size} out of total pages {response_or_error.pages} returned {count} results{ids}')
            elif hasattr(response_or_error, 'count'):
                count = response_or_error.count()
                # Log up to 100 ids, don't log if it's a larger set because it might be a paging query
                ids = R.join(' ',
                             ['', 'having ids:',
                              R.join(', ', R.map(R.prop("id"), response_or_error.values('id')))]) if count < 100 else ""
                logger.debug(f'Query returned {count} results{ids}')
            else:
                id = R.prop('id', response_or_error)
                logger.debug(f'Query returned single result {id}')

    except Exception as e:
        logging.error(body)
