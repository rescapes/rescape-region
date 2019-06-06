from copy import deepcopy

import graphene
from django.db import transaction
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from graphene import InputObjectType, Mutation, Field, List
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field, type_modify_fields
from rescape_graphene.graphql_helpers.json_field_helpers import apply_type
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R
from rescape_graphene import increment_prop_until_unique, enforce_unique_props

from rescape_region.models.project import Project
from rescape_region.schema_models.location_schema import RegionLocationType, location_fields
from rescape_region.schema_models.region_schema import RegionType, region_fields
from .project_data_schema import ProjectDataType, project_data_fields

raw_project_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE, unique_with=increment_prop_until_unique(Project, None, 'key')),
    name=dict(create=REQUIRE),
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
    locations=dict(
        graphene_type=RegionLocationType,
        fields=location_fields,
        type_modifier=lambda *type_and_args: List(*type_and_args)
    )
)


class ProjectType(DjangoObjectType):

    class Meta:
        model = Project


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


class UpsertProject(Mutation):
    """
        Abstract base class for mutation
    """
    project = Field(ProjectType)

    @transaction.atomic
    @login_required
    def mutate(self, info, project_data=None):
        # We must merge in existing project.data if we are updating data
        if R.has('id', project_data) and R.has('data', project_data):
            # New data gets priority, but this is a deep merge.
            project_data['data'] = R.merge_deep(
                Project.objects.get(id=project_data['id']).data,
                project_data['data']
            )

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_project_data = enforce_unique_props(project_fields, project_data)

        # Omit many-to-many locations
        update_or_create_values = input_type_parameters_for_update_or_create(
            project_fields,
            R.omit(['locations'], modified_project_data)
        )

        project, created = Project.objects.update_or_create(**update_or_create_values)
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


graphql_update_or_create_project = graphql_update_or_create(project_mutation_config, project_fields)
graphql_query_projects = graphql_query(ProjectType, project_fields, 'projects')
