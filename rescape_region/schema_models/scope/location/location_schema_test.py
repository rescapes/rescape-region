import logging
from rescape_python_helpers import ramda as R

import pytest
from rescape_graphene import client_for_testing

import os
import django
from reversion.models import Version

from rescape_region.models import Location, Region, Project
from ..project.project_sample import create_sample_projects
from ..region.region_sample import create_sample_regions

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rescape_region.settings")
django.setup()

from rescape_region.model_helpers import get_location_schema
from rescape_region.schema_models.scope.location.location_schema import graphql_update_or_create_location, graphql_query_locations, \
    graphql_query_locations_paginated
from rescape_region.schema_models.schema import create_default_schema
from rescape_graphene.graphql_helpers.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update, quiz_model_paginated_query
from rescape_region.schema_models.user_sample import create_sample_users

from snapshottest import TestCase

from .location_sample import create_local_sample_locations

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['createdAt', 'updatedAt']

schema = create_default_schema()


@pytest.mark.django_db
class LocationSchemaTestCase(TestCase):
    client = None

    def setUp(self):
        users = create_sample_users()
        self.client = client_for_testing(schema, users[0])
        self.locations = create_local_sample_locations(get_location_schema()['model_class'])
        self.regions = create_sample_regions(Region)
        self.projects = create_sample_projects(Project, users, self.regions)
        for project in self.projects:
            project.locations.add(*self.locations)

    def test_query(self):
        quiz_model_query(
            self.client,
            graphql_query_locations,
            'locations',
            dict(
                name='Grand Place',
            )
        )

    def test_query_with_project_reference(self):
        quiz_model_query(
            self.client,
            graphql_query_locations,
            'locations',
            dict(
                name='Grand Place',
                projects=[R.pick(['id'], self.projects[0])]
            )
        )


    def test_query_pagination(self):
        (result, new_result) = quiz_model_paginated_query(
            self.client,
            Location,
            graphql_query_locations_paginated,
            'locationsPaginated',
            2,
            dict(nameContains='Place'),
            omit_props,
            order_by='-name'
        )
        assert result['data']['locationsPaginated']['objects'][0]['name'] == "Petit Place"

    def test_query_order(self):
        result = quiz_model_query(
            self.client,
            graphql_query_locations,
            'locations',
            dict(
                order_by='-name',
            ),
            expect_length=2
        )
        # Check ordering
        assert result['data']['locations'][0]['name'] == 'Petit Place'

    def test_create(self):
        result, new_result = quiz_model_mutation_create(
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
            # Second create should create a new record that matches this regex
            dict(key=r'groteMarkt.+')
        )
        versions = Version.objects.get_for_object(Location.objects.get(
            id=R.item_str_path('data.createLocation.location.id', result)
        ))
        assert len(versions) == 1

    def test_update(self):
        result, update_result = quiz_model_mutation_update(
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
        versions = Version.objects.get_for_object(Location.objects.get(
            id=R.item_str_path('data.updateLocation.location.id', update_result)
        ))
        assert len(versions) == 2
