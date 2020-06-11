from operator import itemgetter

import graphene
from django.db import transaction
from graphene import InputObjectType, Mutation, Field, ObjectType, List
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, UserType, user_fields, allowed_filter_arguments, \
    get_paginator, create_paginated_type_mixin
from rescape_graphene import increment_prop_until_unique, enforce_unique_props
from rescape_graphene.graphql_helpers.schema_helpers import process_filter_kwargs, delete_if_marked_for_delete
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.model_helpers import get_project_model, get_location_schema
from rescape_region.schema_models.region_schema import RegionType, region_fields
from .project_data_schema import ProjectDataType, project_data_fields
from ..models import Project

raw_project_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(get_project_model(), None, 'key', R.pick(['user_id']))),
    name=dict(create=REQUIRE, unique_with=increment_prop_until_unique(get_project_model(), None, 'name', R.pick(['user_id']))),
    created_at=dict(),
    updated_at=dict(),
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
        graphene_type=get_location_schema()['graphene_class'],
        fields=get_location_schema()['graphene_fields'],
        type_modifier=lambda *type_and_args: List(*type_and_args)
    ),
    # This is a Foreign Key. Graphene generates these relationships for us, but we need it here to
    # support our Mutation subclasses and query_argument generation
    user=dict(graphene_type=UserType, fields=user_fields),
    # TODO this needs special authentication to perform writes of deleted=True or reads of deleted=True
    deleted=dict()
)


class ProjectType(DjangoObjectType):
    id = graphene.Int(source='pk')

    class Meta:
        model = get_project_model()


# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
ProjectType._meta.fields['data'] = Field(ProjectDataType, resolver=resolver_for_dict_field)

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
        **allowed_filter_arguments(project_fields, ProjectType)
    )
    projects_paginated = Field(
        ProjectPaginatedType,
        **allowed_filter_arguments(project_paginated_fields, ProjectPaginatedType)
    )

    @login_required
    def resolve_projects(self, info, **kwargs):
        return project_resolver('filter', **kwargs)

    @login_required
    def resolve_projects_paginated(self, info, **kwargs):
        projects = project_resolver('filter', **R.prop_or({}, 'objects', kwargs)).order_by('id')
        return get_paginator(
            projects,
            R.prop('page_size', kwargs),
            R.prop('page', kwargs),
            ProjectPaginatedType
        )


def project_resolver(manager_method, **kwargs):
    """

    Resolves the projects for model get_project_model()
    :param manager_method: 'filter', 'get', or 'count'
    :param kwargs: Filter arguments for the Project
    :return:
    """

    q_expressions = process_filter_kwargs(get_project_model(), kwargs)
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
        deleted_project_response = delete_if_marked_for_delete(Project, UpsertProject, 'project', project_data)
        if deleted_project_response:
            return deleted_project_response

        # We must merge in existing project.data if we are updating data
        if R.has('id', project_data) and R.has('data', project_data):
            # New data gets priority, but this is a deep merge.
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

        project, created = get_project_model().objects.update_or_create(**update_or_create_values)
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


graphql_query_projects_paginated = graphql_query(
    ProjectPaginatedType,
    project_paginated_fields,
    'projectsPaginated'
)
