import logging

from django.core.management import call_command
from rescape_python_helpers import ramda as R

from rescape_graphene import client_for_testing
import pytest
from reversion.models import Version

from rescape_region.models import Region
from rescape_region.schema_models.schema import create_default_schema
from rescape_graphene.graphql_helpers.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update
from rescape_region.schema_models.user_sample import create_sample_users
from .region_schema import graphql_query_regions, graphql_update_or_create_region
from snapshottest import TestCase
from .region_sample import create_sample_regions

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['createdAt', 'updatedAt']

schema = create_default_schema()


@pytest.mark.django_db
class RegionSchemaTestCase(TestCase):
    client = None

    def setUp(self):
        users = create_sample_users()
        self.client = client_for_testing(schema, users[0])
        self.regions = create_sample_regions(Region)

    def test_query(self):
        quiz_model_query(self.client, graphql_query_regions, 'regions', dict(name='Belgium'))

    def test_create(self):
        (result, new_result) = quiz_model_mutation_create(
            self.client, graphql_update_or_create_region, 'createRegion.region',
            dict(
                name='Luxembourg',
                key='luxembourg',
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
                data=dict(
                    locations=dict(
                        params=dict(
                            city='Luxembourg City'
                        )
                    ),
                    # Optional default mapbox settings for the region
                    mapbox=dict(
                        viewport=dict(
                            # Extent can replace latitude, longitude, zoom for complex cases
                            extent=dict(
                                type='FeatureCollection',
                                features=[dict(
                                    type='Feature',
                                    geometry=dict(
                                        type='Polygon',
                                        coordinates=[
                                            [[49.5294835476, 2.51357303225], [51.4750237087, 2.51357303225],
                                             [51.4750237087, 6.15665815596],
                                             [49.5294835476, 6.15665815596], [49.5294835476, 2.51357303225]]]
                                    )
                                )]
                            ),
                        )
                    )
                )
            ),
            dict(key=r'luxembourg.+')
        )
        versions = Version.objects.get_for_object(Region.objects.get(
            id=R.item_str_path('data.createRegion.region.id', result)
        ))
        assert len(versions) == 1

    def test_update(self):
        (result, update_result) = quiz_model_mutation_update(
            self.client,
            graphql_update_or_create_region,
            'createRegion.region',
            'updateRegion.region',
            dict(
                name='Luxembourg',
                key='luxembourg',
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
        versions = Version.objects.get_for_object(Region.objects.get(
            id=R.item_str_path('data.updateRegion.region.id', update_result)
        ))
        assert len(versions) == 2
