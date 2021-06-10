from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType, List
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, UserType, user_fields, \
    create_paginated_type_mixin
from rescape_graphene import increment_prop_until_unique, enforce_unique_props
from rescape_graphene.django_helpers.pagination import resolve_paginated_for_type, pagination_allowed_filter_arguments
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete, \
    update_or_create_with_revision, top_level_allowed_filter_arguments
from rescape_graphene.schema_models.django_object_type_revisioned_mixin import reversion_and_safe_delete_types, \
    DjangoObjectTypeRevisionedMixin
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.model_helpers import get_project_model, get_location_for_project_schema
from rescape_region.schema_models.scope.region.region_schema import RegionType, region_fields
from .project_data_schema import ProjectDataType, project_data_fields

location_type = get_location_for_project_schema()['graphene_class']
location_fields = get_location_for_project_schema()['graphene_fields']

raw_project_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE,
             unique_with=increment_prop_until_unique(get_project_model(), None, 'key', R.pick(['deleted', 'user_id']))),
    name=dict(create=REQUIRE),
    # This refers to the ProjectDataType, which is a representation of all the json fields of Project.data
    data=dict(graphene_type=ProjectDataType, fields=project_data_fields, default=lambda: dict()),
    # This is the OSM geojson
    geojson=dict(
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields
    ),
    region=dict(graphene_type=RegionType, fields=region_fields),
    # The locations of the project. The Graphene type is dynamic to support application specific location classes
    locations=dict(
        graphene_type=lambda: location_type,
        fields=lambda: location_fields,
        type_modifier=lambda *type_and_args: List(*type_and_args)
    ),
    # This is a Foreign Key. Graphene generates these relationships for us, but we need it here to
    # support our Mutation subclasses and query_argument generation
    user=dict(graphene_type=UserType, fields=user_fields),
    **reversion_and_safe_delete_types
)


class ProjectType(DjangoObjectType, DjangoObjectTypeRevisionedMixin):
    id = graphene.Int(source='pk')

    class Meta:
        model = get_project_model()


# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
ProjectType._meta.fields['data'] = Field(
    ProjectDataType,
    resolver=resolver_for_dict_field
)

# Modify the geojson field to use the geometry collection resolver
ProjectType._meta.fields['geojson'] = Field(
    FeatureCollectionDataType,
    resolver=resolver_for_dict_field
)
project_fields = merge_with_django_properties(ProjectType, raw_project_fields)

project_mutation_config = dict(
    class_name='Project',
    crud={
        CREATE: 'createProject',
        UPDATE: 'updateProject'
    },
    resolve=guess_update_or_create
)

# Paginated version of ProjectType
(ProjectPaginatedType, project_paginated_fields) = itemgetter('type', 'fields')(
    create_paginated_type_mixin(ProjectType, project_fields)
)


class ProjectQuery(ObjectType):
    projects = graphene.List(
        ProjectType,
        **top_level_allowed_filter_arguments(project_fields, ProjectType)
    )
    projects_paginated = Field(
        ProjectPaginatedType,
        **pagination_allowed_filter_arguments(project_paginated_fields, ProjectPaginatedType)
    )

    @staticmethod
    def _resolve_projects(info, **kwargs):
        return project_resolver('filter', **kwargs)

    @login_required
    def resolve_projects(self, info, **kwargs):
        return ProjectQuery._resolve_projects(info, **kwargs)

    @login_required
    def resolve_projects_paginated(self, info, **kwargs):
        return resolve_paginated_for_type(
            ProjectPaginatedType,
            ProjectQuery._resolve_projects,
            **kwargs
        )


def project_resolver(manager_method, **kwargs):
    """

    Resolves the projects for model get_project_model()
    :param manager_method: 'filter', 'get', or 'count'
    :param kwargs: Filter arguments for the Project
    :return:
    """

    q_expressions = process_filter_kwargs(get_project_model(), **R.merge(dict(deleted__isnull=True), kwargs))
    return getattr(get_project_model().objects, manager_method)(
        *q_expressions
    )


class UpsertProject(Mutation):
    """
        Abstract base class for mutation
    """
    project = Field(ProjectType)
    @transaction.atomic
    @login_required
    def mutate(self, info, project_data=None):
        deleted_project_response = delete_if_marked_for_delete(get_project_model(), UpsertProject, 'project', project_data)
        if deleted_project_response:
            return deleted_project_response

        # We must merge in existing project.data if we are updating data
        if R.has('id', project_data) and R.has('data', project_data):
            # New data gets priority, but this is a deep merge.
            # If anything is omitted from the new data, it's assumed that the existing value should remain
            project_data['data'] = R.merge_deep(
                get_project_model().objects.get(id=project_data['id']).data,
                project_data['data']
            )

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_project_data = enforce_unique_props(project_fields, project_data)

        # Omit many-to-many locations
        update_or_create_values = input_type_parameters_for_update_or_create(
            project_fields,
            R.omit(['locations'], modified_project_data)
        )

        project, created = update_or_create_with_revision(get_project_model(), update_or_create_values)
        locations = R.prop_or([], 'locations', modified_project_data)
        any_locations = R.compose(R.lt(0), R.length, locations)
        if not created and any_locations:
            # If update and locations are specified, clear the existing ones
            project.locations.clear()

        # Location objects come in as [{id:...}, {id:...}], so pass the id to Django
        if any_locations:
            project.locations.add(*R.map(R.prop('id'), locations))

        return UpsertProject(project=project)


class CreateProject(UpsertProject):
    """
        Create Project mutation class
    """

    class Arguments:
        project_data = type('CreateProjectInputType', (InputObjectType,),
                            input_type_fields(project_fields, CREATE, ProjectType))(required=True)


class UpdateProject(UpsertProject):
    """
        Update Project mutation class
    """

    class Arguments:
        project_data = type('UpdateProjectInputType', (InputObjectType,),
                            input_type_fields(project_fields, UPDATE, ProjectType))(required=True)


class ProjectMutation(graphene.ObjectType):
    create_project = CreateProject.Field()
    update_project = UpdateProject.Field()


graphql_update_or_create_project = graphql_update_or_create(project_mutation_config, project_fields)
graphql_query_projects = graphql_query(ProjectType, project_fields, 'projects')


def graphql_query_projects_limited(project_fields):
    return graphql_query(ProjectType, project_fields, 'projects')


