import logging

import pytest
from django.contrib.auth.hashers import make_password

from rescape_python_helpers import ramda as R
from graphene.test import Client
from snapshottest import TestCase

from rescape_region.models import Region

from rescape_region.schema_models import test_schema, dump_errors
from rescape_region.schema_models import create_sample_user
from .user_state_sample import delete_sample_user_states, create_sample_user_states, \
    form_sample_user_state_data, create_sample_user_state
from .user_state_schema import graphql_query_user_states, graphql_update_or_create_user_state

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['created', 'updated']


@pytest.mark.django_db
class UserStateSchemaTestCase(TestCase):
    client = None
    region = None
    user_state = None

    def setUp(self):
        self.client = Client(test_schema)
        delete_sample_user_states()
        self.user_states = create_sample_user_states()
        # Gather all unique sample users
        self.users = list(set(R.map(
            lambda user_state: user_state.user,
            self.user_states
        )))
        # Gather all unique sample regions
        self.regions = R.compose(
            # Forth Resolve persisted Regions
            R.map(lambda id: Region.objects.get(id=id)),
            # Third make ids unique
            lambda ids: list(set(ids)),
            # Second map each to the region id
            R.map(R.item_str_path('region.id')),
            # First flat map the user regions of all user_states
            R.chain(lambda user_state: R.item_str_path('data.user_regions', user_state.__dict__))
        )(self.user_states)

    def test_query(self):
        all_results = graphql_query_user_states(self.client)
        assert not R.has('errors', all_results), R.dump_json(R.prop('errors', all_results))

    def test_filter_query(self):
        # Make sure that we can filter. Here we are filtered on the User related to UserState
        # That's why we need the complex class UserTypeofUserStateTypeRelatedReadInputType
        # I'd like this to just be UserReadInputType but Graphene forces us to use unique types for input classes
        # throughout the schema, even if they represent the same underlying model class or json blob structure
        results = graphql_query_user_states(self.client,
                                            dict(user='UserTypeofUserStateTypeRelatedReadInputType'),
                                            variable_values=dict(user=R.pick(['id'], self.users[0].__dict__)))
        # Check against errors
        assert not R.has('errors', results), R.dump_json(R.prop('errors', results))
        assert 1 == R.length(R.item_path(['data', 'userStates'], results))

    def test_create(self):
        # First add a new User
        margay = dict(username="margay", first_name='Upa', last_name='Tree',
                      password=make_password("merowgir", salt='not_random'))
        user = create_sample_user(margay)
        # Now assign regions and persist the UserState
        sample_user_data = form_sample_user_state_data(
            self.regions,
            dict(
                user_regions=[
                    dict(
                        # Assign the first region
                        region=dict(key=R.prop('key', R.head(self.regions))),
                        mapbox=dict(viewport=dict(
                            latitude=50.5915,
                            longitude=2.0165,
                            zoom=7
                        ))
                    )
                ]
            )
        )

        values = dict(
            user=R.pick(['id'], user.__dict__),
            data=sample_user_data
        )
        result = graphql_update_or_create_user_state(self.client, values)
        dump_errors(result)
        assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
        # Don't worry about ids since they can be different as we write more tests
        self.assertMatchSnapshot(R.omit_deep(omit_props + ['id'], result))

    def test_update(self):
        # Create the sample User
        margay = dict(username="margay", first_name='Upa', last_name='Tree',
                      password=make_password("merowgir", salt='not_random'))
        user = create_sample_user(margay)

        # Now assign regions and persist the UserState
        user_state = create_sample_user_state(
            self.regions,
            dict(
                username=user.username,
                data=dict(
                    user_regions=[
                        dict(
                            # Assign the first region
                            region=dict(key=R.prop('key', R.head(self.regions))),
                            mapbox=dict(viewport=dict(
                                latitude=50.5915,
                                longitude=2.0165,
                                zoom=5
                            ))
                        )
                    ]
                )
            )
        )

        user_state_values = dict(
            user=R.pick(['id'], user_state.user.__dict__),
            data=user_state.data,
            id=user_state.id
        )
        # Update the zoom
        R.item_str_path('mapbox.viewport', R.head(R.item_str_path('data.user_regions', user_state_values)))['zoom'] = 7
        update_result = graphql_update_or_create_user_state(self.client, user_state_values)
        dump_errors(update_result)
        assert not R.has('errors', update_result), R.dump_json(R.prop('errors', update_result))
        # Assert same instance
        updated_user_state = R.item_str_path('data.updateUserState.userState', update_result)
        assert updated_user_state['id'] == str(user_state_values['id'])
        # Assert the viewport updated
        assert R.item_str_path('data.userRegions.0.mapbox.viewport.zoom', updated_user_state) == 7

    # def test_delete(self):
    #     self.assertMatchSnapshot(self.client.execute('''{
    #         user_states {
    #             username,
    #             first_name,
    #             last_name,
    #             password
    #         }
    #     }'''))
