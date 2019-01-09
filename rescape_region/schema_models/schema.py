from functools import partial

import graphene
import logging
import sys
import traceback

from graphene_django.filter.utils import get_filterset_class, get_filtering_args_from_filterset
from graphql import format_error
from rescape_graphene.graphql_helpers.schema_helpers import stringify_query_kwargs, allowed_filter_arguments, process_filter_kwargs
from rescape_python_helpers import ramda as R
import graphql_jwt
from graphene import ObjectType, Schema, Field, List
from graphql_jwt.decorators import login_required
from rescape_graphene import group_fields, GroupType, Mutation, Query
from rescape_graphene import CreateUser, UpdateUser, UserType, user_fields
from rescape_region.models import Region, UserState, GroupState
from rescape_region.schema_models.group_state_schema import GroupStateType, group_state_fields
from rescape_region.schema_models.region_schema import RegionType, region_fields, CreateRegion, UpdateRegion
from rescape_region.schema_models.user_state_schema import user_state_fields, UserStateType, CreateUserState, \
    UpdateUserState

logger = logging.getLogger('rescape-region')


class DjangoFilterField(Field):
    """
    Custom field to use django-filter with graphene object types (without relay).
    """

    def __init__(self, _type, fields=None, extra_filter_meta=None,
                 filterset_class=None, *args, **kwargs):
        _fields = _type._meta.filter_fields
        _model = _type._meta.model
        self.of_type = _type
        self.fields = fields or _fields
        meta = dict(model=_model, fields=self.fields)
        if extra_filter_meta:
            meta.update(extra_filter_meta)
        self.filterset_class = get_filterset_class(filterset_class, **meta)
        self.filtering_args = get_filtering_args_from_filterset(
            self.filterset_class, _type)
        kwargs.setdefault('args', {})
        kwargs['args'].update(self.filtering_args)
        super().__init__(List(_type), *args, **kwargs)

    @staticmethod
    def list_resolver(manager, filterset_class, filtering_args, root, info, *args, **kwargs):
        filter_kwargs = {k: v for k,
                                  v in kwargs.items() if k in filtering_args}
        qs = manager.get_queryset()
        qs = filterset_class(data=filter_kwargs, queryset=qs).qs
        return qs

    def get_resolver(self, parent_resolver):
        return partial(self.list_resolver, self.of_type._meta.model._default_manager,
                       self.filterset_class, self.filtering_args)


class LocalQuery(ObjectType):
    regions = graphene.List(
        RegionType,
        **allowed_filter_arguments(region_fields, RegionType)
    )

    user_states = graphene.List(
        UserStateType,
        **allowed_filter_arguments(user_state_fields, UserStateType)
    )

    group_states = graphene.List(
        GroupStateType,
        **allowed_filter_arguments(group_state_fields, GroupStateType)
    )


    @login_required
    def resolve_regions(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(kwargs)

        # Small correction here to change the data filter to data__contains to handle any json
        # https://docs.djangoproject.com/en/2.0/ref/contrib/postgres/fields/#std:fieldlookup-hstorefield.contains
        # This is just one way of filtering json. We can also do it with the argument structure
        return Region.objects.filter(
            deleted__isnull=True,
            **R.map_keys(lambda key: str.join('__', [key, 'contains']) if R.contains(key, ['data', 'geojson']) else key,
                         modified_kwargs))

    @login_required
    def resolve_user_states(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(kwargs)

        return UserState.objects.filter(
            **stringify_query_kwargs(UserState, modified_kwargs)
        )

    @login_required
    def resolve_group_states(self, info, **kwargs):
        modified_kwargs = process_filter_kwargs(kwargs)

        return GroupState.objects.filter(
            **stringify_query_kwargs(GroupState, modified_kwargs)
        )


class LocalMutation(graphene.ObjectType):
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


class Query(LocalQuery, Query):
    """
        Merge the rescape-region query with our local query
    """
    pass


class Mutation(LocalMutation, Mutation):
    """
        Merge the rescape-region mutation with our local mutations
    """
    pass


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
