from django.contrib.auth import get_user_model
from rescape_python_helpers import ramda as R

from rescape_region.models import UserState
from rescape_region.schema_models.scope.location.location_sample import create_local_sample_locations, \
    create_local_sample_search_locations
from rescape_region.schema_models.scope.project.project_sample import create_sample_projects
from rescape_region.schema_models.scope.region.region_sample import create_sample_regions
from rescape_region.schema_models.user_sample import create_sample_users

sample_user_states = [
    dict(
        username="lion",  # This is converted to a user=persisted User
        data=dict(
            userGlobal=dict(
                mapbox=dict(viewport=dict(
                    latitude=50.5915,
                    longitude=2.0165,
                    zoom=7
                )),
            ),
            userRegions=[
                dict(
                    region=dict(key='belgium'),  # key is converted to persisted Region's id
                    mapbox=dict(viewport=dict(
                        latitude=50.5915,
                        longitude=2.0165,
                        zoom=7
                    )),
                )
            ],
            userProjects=[
                dict(
                    project=dict(key='gare'),  # key is converted to persisted Project's id
                    mapbox=dict(viewport=dict(
                        latitude=50.846127,
                        longitude=4.358111,
                        zoom=10
                    )),
                )
            ]
        )
    ),
    dict(
        username="cat",  # This is converted to a user=persisted User
        data=dict(
            userGlobal=dict(
                mapbox=dict(viewport=dict(
                    latitude=50.5915,
                    longitude=2.0165,
                    zoom=7
                )),
            ),
            userRegions=[
                dict(
                    region=dict(key='belgium'),  # key is converted to persisted Region's id
                    mapbox=dict(viewport=dict(
                        latitude=50.5915,
                        longitude=2.0165,
                        zoom=7
                    )),
                )
            ],
            userProjects=[
                dict(
                    project=dict(key='gare'),  # key is converted to persisted Project's id
                    mapbox=dict(viewport=dict(
                        latitude=50.846127,
                        longitude=4.358111,
                        zoom=10
                    )),
                )
            ]
        )
    )
]


def delete_sample_user_states():
    UserState.objects.all().delete()


@R.curry
def create_sample_user_state(cls, regions, projects, user_state_dict):
    """
    Persists sample user state data into a UserState
    :param cls: The UserState class
    :param {[Region]} regions: Persisted sample regions
    :param {[Projects]} projects: Persisted sample projects
    :param user_state_dict: Sample data in the form: dict(
        username="lion",  # This will be mapped to the User id in create_sample_user_state
        data=dict(
            userRegions=[
                dict(
                    region=dict(key='belgium'),  # key is converted to persisted Region's id
                    mapbox=dict(viewport=dict(
                        latitude=50.5915,
                        longitude=2.0165,
                        zoom=7
                    )),
                )
            ]
        )
    ),
    :param locations
    :param search_locations Search locations that match 0 or more locations
    :return:
    """
    user = get_user_model().objects.get(username=user_state_dict['username'])
    user_state_values = R.merge_deep(
        # Skip username and data, they are handled above and below
        R.omit(['username', 'data'], user_state_dict),
        # Convert data.region_keys to data.user_region ids
        dict(
            user=user,
            data=form_sample_user_state_data(
                regions,
                projects,
                R.prop(
                    'data',
                    user_state_dict
                )
            )
        )
    )
    # Save the user_state with the complete data
    user_state = cls(**user_state_values)
    user_state.save()
    return user_state


def user_state_scope_instances(scope_key, user_scope_key, scope_instances, data):
    """
        Creates scope instance dicts for the given instances
    :param scope_key: 'region', 'project', etc
    :param user_scope_key: 'userRegions', 'userProjects', etc
    :param scope_instances: regions or projects or ...
    :param data: The userState data to put the instances in. E.g. data.userRegions gets mapped to include
    the resolved regions
    :return:
    """

    scope_instances_by_key = R.map_prop_value_as_index('key', scope_instances)
    return R.map(
        # Find the id of th scope instance that matches,
        # returning dict(id=scope_instance_id). We can't return the whole scope instance
        # because we are saving within json data, not the Django ORM
        lambda user_scope_instance: R.merge(
            # Other stuff like mapbox
            R.omit([scope_key], user_scope_instance),
            # Replace key with id
            {
                scope_key: dict(
                    # Resolve the persisted Scope instance by key
                    id=R.compose(
                        # third get the id
                        R.prop('id'),
                        # second resolve the scope instance
                        lambda k: R.prop(k, scope_instances_by_key),
                        # first get the key
                        R.item_str_path(f'{scope_key}.key')
                    )(user_scope_instance)
                )
            }
        ),
        R.prop(user_scope_key, data)
    )


def form_sample_user_state_data(regions, projects, data):
    """
    Given data in the form dict(region_keys=[...], ...), converts region_keys to
    regions=[{id:x}, {id:y}, ...] by resolving the regions
    :param regions: Persisted regions
    :param projects: Persisted projects
    :param {dict} data: Sample data in the form:
    dict(
        userRegions=[
            dict(
                region=dict(key='belgium'),  # key is converted to persisted Region's id
                mapbox=dict(viewport=dict(
                    latitude=50.5915,
                    longitude=2.0165,
                    zoom=7
                )),
            )
        ]
    ),
    :return: Data in the form dict(userRegions=[dict(region=dict(id=x), mapbox=..., ...), ...])
    """
    return R.merge(
        # Rest of data that's not regions
        R.omit(['userRegions', 'userProjects'], data),
        dict(
            userRegions=user_state_scope_instances('region', 'userRegions', regions, data),
            userProjects=user_state_scope_instances('project', 'userProjects', projects, data)
        )
    )


def create_sample_user_states(
        cls, region_cls, project_cls, location_cls, search_location_cls,
        create_sample_locations=create_local_sample_locations,
        create_sample_search_locations=create_local_sample_search_locations,
        create_additional_scope_instance_properties=lambda user_scope_instance: user_scope_instance
):
    """
    :param cls: The UserState class
    :param region_cls:
    :param project_cls:
    :param location_cls:
    :param search_location_cls:
    :param create_sample_locations: Defaults to create_local_sample_locations. Expects
    the location_cls as the only arg
    :param create_search_sample_locations: Defaults to create_local_sample_search_locations. Expects
    the serach_location_cls and a list of sample locations. The locations can be ignored
    if creating samples independent of the locations
    :param create_additional_scope_instance_properties Function that takes each user_scope_instance
    and adds properties to it if needed. This corresponds with schemas defined by users in
    additional_user_scope_schemas
    :return:
    """
    users = create_sample_users()
    # Create regions for the users to associate with. A region also needs and owner so we pass users to the function
    regions = create_sample_regions(region_cls)
    projects = create_sample_projects(project_cls, users, regions)
    locations = create_sample_locations(location_cls)
    search_locations = create_sample_search_locations(search_location_cls, locations)
    # Assign all the locations to each project
    for project in projects:
        project.locations.add(*locations)

    # Merge search_locations into each userScope dict
    def sample_user_state_with_search_locations_and_additional_scope_instances(user_scope_name, sample_user_state):
        return R.fake_lens_path_set(
            f'data.{user_scope_name}'.split('.'),
            R.map(
                lambda user_scope: R.compose(
                    # Gives applications a chance to add the needed additional scope instances,
                    # e.g. userDesignFeatures
                    lambda user_scope: create_additional_scope_instance_properties(user_scope),
                    lambda user_scope: R.merge(
                        user_scope,
                        dict(
                            userSearch=dict(
                                userSearchLocations=R.map(lambda i_search_location: dict(
                                    # Just return with the id since the full data is in the database
                                    searchLocation=R.pick(['id'], i_search_location[1]),
                                    # Set the first search_location to active
                                    activity=dict(isActive=i_search_location[0] == 0)
                                ), enumerate(search_locations))
                            )
                        )
                    )
                )(user_scope),
                R.item_str_path(f'data.{user_scope_name}', sample_user_state)
            ),
            sample_user_state
        )

    # Convert all sample user_state dicts to persisted UserState instances
    # Use the username to match a real user
    user_states = R.map(
        lambda sample_user_state: create_sample_user_state(cls, regions, projects, sample_user_state),
        # Adds search_locations to each userState.data.[userRegions[*]|userProjects[*]].user_search.userSearchLocations
        R.compose(
            lambda sample_user_states: R.map(
                lambda sample_user_state: sample_user_state_with_search_locations_and_additional_scope_instances(
                    'userProjects', sample_user_state),
                sample_user_states
            ),
            lambda sample_user_states: R.map(
                lambda sample_user_state: sample_user_state_with_search_locations_and_additional_scope_instances(
                    'userRegions', sample_user_state),
                sample_user_states
            ),
        )(sample_user_states)
    )
    return user_states
