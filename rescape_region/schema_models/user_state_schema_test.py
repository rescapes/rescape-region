import logging
from copy import deepcopy

import pytest
from django.contrib.auth.hashers import make_password
from rescape_graphene import client_for_testing
from rescape_python_helpers import ramda as R
from snapshottest import TestCase

from rescape_region.model_helpers import get_region_model, get_project_model, \
    get_location_schema
from rescape_region.models import UserState
from rescape_region.schema_models.project_schema import project_fields, ProjectType
from rescape_region.schema_models.region_schema import RegionType, region_fields
from rescape_region.schema_models.schema import create_schema
from rescape_region.schema_models.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update
from rescape_region.schema_models.user_sample import create_sample_user
from rescape_region.schema_models.user_state_schema import create_user_state_config
from .user_state_sample import delete_sample_user_states, create_sample_user_states, \
    form_sample_user_state_data

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['created', 'updated', 'createdAt', 'updatedAt', 'dateJoined']

schema = create_schema()
default_class_config = dict(
    region=dict(
        model_class=get_region_model(),
        graphene_class=RegionType,
        graphene_fields=region_fields
    ),
    project=dict(
        model_class=get_project_model(),
        graphene_class=ProjectType,
        graphene_fields=project_fields
    ),
    location=dict(
        model_class=get_location_schema()['model_class'],
        graphene_class=get_location_schema()['graphene_class'],
        graphene_fields=get_location_schema()['graphene_fields']
    )
)
user_state_schema = create_user_state_config(default_class_config)


@pytest.mark.django_db
class UserStateSchemaTestCase(TestCase):
    client = None
    region = None
    user_state = None

    def setUp(self):
        delete_sample_user_states()
        self.user_states = create_sample_user_states(UserState, get_region_model(), get_project_model())
        # Gather all unique sample users
        self.users = list(set(R.map(
            lambda user_state: user_state.user,
            self.user_states
        )))
        self.client = client_for_testing(schema, self.users[0])
        # Gather all unique sample regions
        self.regions = R.compose(
            # Forth Resolve persisted Regions
            R.map(lambda id: get_region_model().objects.get(id=id)),
            # Third make ids unique
            lambda ids: list(set(ids)),
            # Second map each to the region id
            R.map(R.item_str_path('region.id')),
            # First flat map the user regions of all user_states
            R.chain(lambda user_state: R.item_str_path('data.userRegions', user_state.__dict__))
        )(self.user_states)
        # Gather all unique sample projects
        self.projects = R.compose(
            # Forth Resolve persisted Projects
            R.map(lambda id: get_project_model().objects.get(id=id)),
            # Third make ids unique
            lambda ids: list(set(ids)),
            # Second map each to the project id
            R.map(R.item_str_path('project.id')),
            # First flat map the user regions of all user_states
            R.chain(lambda user_state: R.item_str_path('data.userProjects', user_state.__dict__))
        )(self.user_states)

    def test_query(self):
        quiz_model_query(
            self.client,
            R.prop('graphql_query', user_state_schema),
            'userStates',
            dict(user=dict(id=R.prop('id', R.head(self.users))))
        )

    def test_create(self):
        # First add a new User
        margay = dict(username="margay", first_name='Upa', last_name='Tree',
                      password=make_password("merowgir", salt='not_random'))
        user = create_sample_user(margay)

        # Now assign regions and persist the UserState
        sample_user_state_data = dict(
            user=dict(id=user.id),
            data=form_sample_user_state_data(
                self.regions,
                self.projects,
                dict(
                    userGlobal=dict(
                        mapbox=dict(viewport=dict(
                            latitude=50.5915,
                            longitude=2.0165,
                            zoom=7
                        ))
                    ),
                    userRegions=[
                        dict(
                            # Assign the first region
                            region=dict(
                                key=R.prop('key', R.head(self.regions))
                            ),
                            mapbox=dict(viewport=dict(
                                latitude=50.5915,
                                longitude=2.0165,
                                zoom=7
                            ))
                        )
                    ],
                    userProjects=[
                        dict(
                            # Assign the first prjoect
                            project=dict(key=R.prop('key', R.head(self.projects))),
                            mapbox=dict(viewport=dict(
                                latitude=50.5915,
                                longitude=2.0165,
                                zoom=7
                            ))
                        )
                    ]
                )
            )
        )

        quiz_model_mutation_create(
            self.client,
            R.prop('graphql_mutation', user_state_schema),
            'createUserState.userState',
            sample_user_state_data,
            # The second create should update, since we can only have one userState per user
            dict(),
            True
        )

    def test_update(self):
        # First add a new User
        margay = dict(username="margay", first_name='Upa', last_name='Tree',
                      password=make_password("merowgir", salt='not_random'))
        user = create_sample_user(margay)

        # Now assign regions and persist the UserState
        sample_user_state_data = dict(
            user=dict(id=user.id),
            data=form_sample_user_state_data(
                self.regions,
                self.projects,
                dict(
                    userRegions=[
                        dict(
                            # Assign the first region
                            region=dict(key=R.prop('key', R.head(self.regions))),
                            mapbox=dict(viewport=dict(
                                latitude=50.5915,
                                longitude=2.0165,
                                zoom=7
                            ))
                        )
                    ],
                    userProjects=[
                        dict(
                            # Assign the first prjoect
                            project=dict(key=R.prop('key', R.head(self.projects))),
                            mapbox=dict(viewport=dict(
                                latitude=50.5915,
                                longitude=2.0165,
                                zoom=7
                            ))
                        )
                    ]
                )
            )
        )

        # Update the zoom of the first userRegion
        update_data = deepcopy(R.pick(['data'], sample_user_state_data))
        R.item_str_path('mapbox.viewport', R.head(R.item_str_path('data.userRegions', (update_data))))['zoom'] = 15

        quiz_model_mutation_update(
            self.client,
            R.prop('graphql_mutation', user_state_schema),
            'createUserState.userState',
            'updateUserState.userState',
            sample_user_state_data,
            update_data
        )

    # def test_delete(self):
    #     self.assertMatchSnapshot(self.client.execute('''{
    #         user_states {
    #             username,
    #             first_name,
    #             last_name,
    #             password
    #         }
    #     }'''))
