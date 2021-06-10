import logging

import pytest
from rescape_graphene import client_for_testing
from rescape_python_helpers import ramda as R
from reversion.models import Version

from rescape_region.model_helpers import get_location_schema, get_project_model
from rescape_region.models.region import Region

from rescape_region.schema_models.scope.location.location_sample import create_local_sample_locations
from rescape_region.schema_models.scope.region.region_sample import create_sample_regions
from rescape_region.schema_models.schema import create_default_schema
from rescape_graphene.graphql_helpers.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update
from rescape_region.schema_models.user_sample import create_sample_users

from snapshottest import TestCase

from .project_sample import create_sample_projects
from .project_schema import graphql_query_projects, graphql_update_or_create_project

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['createdAt', 'updatedAt']




@pytest.mark.django_db
class ProjectSchemaTestCase(TestCase):
    client = None

    def setUp(self):
        schema = create_default_schema()
        self.users = create_sample_users()
        self.client = client_for_testing(schema, self.users[0])
        regions = create_sample_regions(Region)
        self.projects = create_sample_projects(get_project_model(), self.users, regions)
        self.locations = create_local_sample_locations(get_location_schema()['model_class'])

    def test_query(self):
        quiz_model_query(self.client, graphql_query_projects, 'projects', dict(name='Gare'))

    def test_create(self):
        result, new_result = quiz_model_mutation_create(
            self.client, graphql_update_or_create_project, 'createProject.project',
            dict(
                name='Carre',
                key='carre',
                geojson={
                    'type': 'FeatureCollection',
                    'features': [{
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[49.5294835476, 2.51357303225], [51.4750237087, 2.51357303225],
                                 [51.4750237087, 6.15665815596],
                                 [49.5294835476, 6.15665815596], [49.5294835476, 2.51357303225]]]
                        }
                    }]
                },
                data=dict(),
                locations=R.map(R.compose(R.pick(['id']), lambda l: l.__dict__), self.locations),
                user=R.pick(['id'], R.head(self.users).__dict__),
            ),
            dict(key=r'carre.+'))
        versions = Version.objects.get_for_object(get_project_model().objects.get(
            id=R.item_str_path('data.createProject.project.id', result)
        ))
        assert len(versions) == 1

    def test_update(self):
        result, update_result = quiz_model_mutation_update(
            self.client,
            graphql_update_or_create_project,
            'createProject.project',
            'updateProject.project',
            dict(
                name='Carre',
                key='carre',
                geojson={
                    'type': 'FeatureCollection',
                    'features': [{
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[49.4426671413, 5.67405195478], [50.1280516628, 5.67405195478],
                                 [50.1280516628, 6.24275109216],
                                 [49.4426671413, 6.24275109216], [49.4426671413, 5.67405195478]]]
                        }
                    }]
                },
                data=dict(),
                locations=R.map(R.compose(R.pick(['id']), lambda l: l.__dict__), self.locations),
                user=R.pick(['id'], R.head(self.users).__dict__),
            ),
            # Update the coords and limit to one location
            dict(
                geojson={
                    'features': [{
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[49.5294835476, 2.51357303225], [51.4750237087, 2.51357303225],
                                 [51.4750237087, 6.15665815596],
                                 [49.5294835476, 6.15665815596], [49.5294835476, 2.51357303225]]]
                        }
                    }]
                },
                locations=R.map(R.compose(R.pick(['id']), lambda l: l.__dict__), [R.head(self.locations)])
            )
        )
        versions = Version.objects.get_for_object(get_project_model().objects.get(
            id=R.item_str_path('data.updateProject.project.id', update_result)
        ))
        assert len(versions) == 2
