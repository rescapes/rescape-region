import logging

import pytest
from rescape_graphene import client_for_testing

from rescape_region.models import Location
from rescape_region.schema_models.schema import create_schema
from rescape_region.schema_models.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update
from rescape_region.schema_models.user_sample import create_sample_users
from .location_schema import graphql_query_locations, graphql_update_or_create_location

from snapshottest import TestCase

from .location_sample import create_sample_locations

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['createdAt', 'updatedAt']

schema = create_schema()
@pytest.mark.django_db
class LocationSchemaTestCase(TestCase):
    client = None

    def setUp(self):
        users = create_sample_users()
        self.client = client_for_testing(schema, users[0])
        self.locations = create_sample_locations(Location)

    def test_query(self):
        quiz_model_query(self.client, graphql_query_locations, 'locations', dict(name='Grand Place'))

    def test_create(self):
        quiz_model_mutation_create(
            self.client,
            graphql_update_or_create_location,
            'createLocation.location',
            dict(
                name='Grote Markt',
                key='groteMarkt',
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
            ),
            # Second create should create a new record with a unique key
            dict(key='groteMarkt1')
        )

    def test_update(self):
        quiz_model_mutation_update(
            self.client,
            graphql_update_or_create_location,
            'createLocation.location',
            'updateLocation.location',
            dict(
                name='Grote Markt',
                key='groteMarkt',
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
            ),
            # Update the coords
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
                }
            )
        )
