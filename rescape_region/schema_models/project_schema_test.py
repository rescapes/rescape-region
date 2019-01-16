import logging

import pytest
from rescape_graphene import client_for_testing
from rescape_python_helpers import ramda as R

from rescape_region.schema_models.schema import schema
from rescape_region.schema_models.user_sample import create_sample_users
from .project_schema import graphql_query_projects, graphql_update_or_create_project

from snapshottest import TestCase

from .project_sample import create_sample_projects

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['createdAt', 'updatedAt']


@pytest.mark.django_db
class ProjectSchemaTestCase(TestCase):
    client = None

    def setUp(self):
        users = create_sample_users()
        self.client = client_for_testing(schema, users[0])
        self.projects = create_sample_projects()

    def test_query(self):
        all_result = graphql_query_projects(self.client)
        assert not R.has('errors', all_result), R.dump_json(R.prop('errors', all_result))
        result = graphql_query_projects(
            self.client,
            variables=dict(name='Gare')
        )
        # Check against errors
        assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
        # Visual assertion that the query looks good
        assert 1 == R.length(R.item_path(['data', 'projects'], result))

    def test_create(self):
        values = dict(
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
            data=dict()
        )
        result = graphql_update_or_create_project(self.client, values)
        result_path_partial = R.item_path(['data', 'createProject', 'project'])
        assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
        created = result_path_partial(result)
        # look at the users added and omit the non-determinant dateJoined
        self.assertMatchSnapshot(R.omit_deep(omit_props, created))
        # Try creating the same project again, because of the unique constraint on key and the unique_with property
        # on its field definition value, it will increment to luxembourg1
        new_result = graphql_update_or_create_project(self.client, values)
        assert not R.has('errors', new_result), R.dump_json(R.prop('errors', new_result))
        created_too = result_path_partial(new_result)
        assert created['id'] != created_too['id']
        assert created_too['key'] == 'carre1'

    def test_update(self):
        values = dict(
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
            data=dict()
        )
        result = graphql_update_or_create_project(self.client, values)
        result_path_partial = R.item_path(['data', 'createProject', 'project'])
        assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
        created = result_path_partial(result)
        # look at the users added and omit the non-determinant dateJoined
        self.assertMatchSnapshot(R.omit_deep(omit_props, created))
        # Try updating the project, changing the coordinates
        updated_result = graphql_update_or_create_project(
            self.client,
            R.merge(
                dict(id=int(created['id']),
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
                     }),
                values
            )
        )
        assert not R.has('errors', updated_result), R.dump_json(R.prop('errors', updated_result))
        result_path_partial = R.item_path(['data', 'updateProject', 'project'])
        updated = result_path_partial(updated_result)
        assert created['id'] == updated['id']
        assert updated['key'] == 'carre'
