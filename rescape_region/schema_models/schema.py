import graphene
import logging
import sys
import traceback
from graphql import format_error
from rescape_graphene.graphql_helpers.schema_helpers import stringify_query_kwargs
from rescape_python_helpers import ramda as R
import graphql_jwt
from graphene import ObjectType, Schema
from graphene_django.debug import DjangoDebug
# from graphql_jwt.decorators import login_required
from graphql_jwt.decorators import login_required
from rescape_graphene import allowed_query_arguments, group_fields, GroupType
from rescape_graphene import CreateUser, UpdateUser, UserType, user_fields
from django.contrib.auth import get_user_model, get_user

from rescape_region.models import Region, UserState, GroupState
from rescape_region.schema_models.group_state_schema import GroupStateType, group_state_fields
from rescape_region.schema_models.region_schema import RegionType, region_fields, CreateRegion, UpdateRegion
from rescape_region.schema_models.user_state_schema import user_state_fields, UserStateType, CreateUserState, \
    UpdateUserState

logger = logging.getLogger('rescape-region')


class Query(ObjectType):
    # This causes problems with remote query introspection because of the __
    # debug = graphene.Field(DjangoDebug, name='__debug')
    users = graphene.List(
        UserType,
        **allowed_query_arguments(user_fields, UserType)
    )

    groups = graphene.List(
        UserType,
        **allowed_query_arguments(group_fields, GroupType)
    )

    viewer = graphene.Field(
        UserType,
        **allowed_query_arguments(user_fields, UserType)
    )

    @login_required
    def resolve_viewer(self, info, **kwargs):
        return info.context.user

    regions = graphene.List(
        RegionType,
        **allowed_query_arguments(region_fields, RegionType)
    )

    region = graphene.Field(
        RegionType,
        **allowed_query_arguments(region_fields, RegionType)
    )

    user_states = graphene.List(
        UserStateType,
        **allowed_query_arguments(user_state_fields, UserStateType)
    )

    user_state = graphene.Field(
        UserStateType,
        **allowed_query_arguments(user_state_fields, UserStateType)
    )

    group_states = graphene.List(
        GroupStateType,
        **allowed_query_arguments(group_state_fields, GroupStateType)
    )

    group_state = graphene.Field(
        GroupStateType,
        **allowed_query_arguments(group_state_fields, GroupStateType)
    )

    def resolve_users(self, info, **kwargs):
        return get_user_model().objects.filter(**kwargs)

    def resolve_current_user(self, info):
        context = info.context
        user = get_user(context)
        if not user:
            raise Exception('Not logged in!')

        return user

    def resolve_regions(self, info, **kwargs):
        # Small correction here to change the data filter to data__contains to handle any json
        # https://docs.djangoproject.com/en/2.0/ref/contrib/postgres/fields/#std:fieldlookup-hstorefield.contains
        return Region.objects.filter(
            deleted__isnull=True,
            **R.map_keys(lambda key: 'data__contains' if R.equals('data', key) else key, kwargs))

    def resolve_user_states(self, info, **kwargs):
        return UserState.objects.filter(
            **stringify_query_kwargs(UserState, kwargs)
        )

    def resolve_group_states(self, info, **kwargs):
        return GroupState.objects.filter(
            **stringify_query_kwargs(GroupState, kwargs)
        )

    def resolve_region(self, info, **kwargs):
        return Region.objects.get(
            **stringify_query_kwargs(Region, kwargs)
        )

    def resolve_user_state(self, info, **kwargs):
        return UserState.objects.get(
            **stringify_query_kwargs(UserState, kwargs)
        )

    def resolve_group_state(self, info, **kwargs):
        return GroupState.objects.get(
            **stringify_query_kwargs(GroupState, kwargs)
        )


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    # login = Login.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    create_region = CreateRegion.Field()
    update_region = UpdateRegion.Field()

    create_user_state = CreateUserState.Field()
    update_user_state = UpdateUserState.Field()


schema = Schema(query=Query, mutation=Mutation)


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
