import logging
from rescape_python_helpers import ramda as R

import pytest
from rescape_graphene import client_for_testing
from reversion.models import Version

from rescape_region.models.settings import Settings
from rescape_region.schema_models.schema import create_default_schema
from rescape_graphene.graphql_helpers.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update
from rescape_region.schema_models.settings.setttings_sample import create_sample_settings_sets
from rescape_region.schema_models.user_sample import create_sample_users
from .settings_schema import graphql_query_settings, graphql_update_or_create_settings
from snapshottest import TestCase

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['createdAt', 'updatedAt']

schema = create_default_schema()


@pytest.mark.django_db
class SettingsSchemaTestCase(TestCase):
    client = None

    def setUp(self):
        users = create_sample_users()
        self.client = client_for_testing(schema, users[0])
        self.settings = create_sample_settings_sets(Settings)

    def test_query(self):
        quiz_model_query(self.client, graphql_query_settings, 'settings', dict(key='global'))

    def test_create(self):
        result, _ = quiz_model_mutation_create(
            self.client, graphql_update_or_create_settings, 'createSettings.settings',
            dict(
                key='mars',
                data=dict(
                    domain='localhost',
                    api=dict(
                        protocol='http',
                        host='localhost',
                        port='8008',
                        path='/graphql/'
                    ),
                    overpass=dict(
                        cellSize=100,
                        sleepBetweenCalls=1000
                    ),
                    mapbox=dict(
                        viewport={},
                    )
                )
            )
        )
        versions = Version.objects.get_for_object(Settings.objects.get(
            id=R.item_str_path('data.createSettings.settings.id', result)
        ))
        assert len(versions) == 1

    def test_update(self):
        result, update_result = quiz_model_mutation_update(
            self.client,
            graphql_update_or_create_settings,
            'createSettings.settings',
            'updateSettings.settings',
            dict(
                key='mars',
                data=dict(
                    domain='localhost',
                    api=dict(
                        protocol='http',
                        host='localhost',
                        port='8008',
                        path='/graphql/'
                    ),
                    overpass=dict(
                        cellSize=100,
                        sleepBetweenCalls=1000
                    ),
                    mapbox=dict(
                        viewport={},
                    )
                )
            ),
            # Update the coords
            dict(
                data=dict(
                    domain='alienhost',
                    api=dict(
                        host='alienhost',
                    )
                )
            )
        )
        versions = Version.objects.get_for_object(Settings.objects.get(
            id=R.item_str_path('data.updateSettings.settings.id', update_result)
        ))
        assert len(versions) == 2
