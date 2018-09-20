
from django.contrib.auth import get_user_model
from rescape_python_helpers import ramda as R

from rescape_region.models import UserState
from rescape_region.schema_models.region_sample import create_sample_regions
from rescape_region.schema_models.user_sample import create_sample_users

sample_user_states = [
    dict(
        username="lion",  # This is converted to a user=persisted User
        data=dict(
            user_regions=[
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
    dict(
        username="cat",  # This is converted to a user=persisted User
        data=dict(
            user_regions=[
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
    )
]


def delete_sample_user_states():
    UserState.objects.all().delete()


@R.curry
def create_sample_user_state(regions, user_state_dict):
    """
    Persists sample user state data into a UserState
    :param {[Region]} regions: Persisted sample regions
    :param user_state_dict: Sample data in the form: dict(
        username="lion",  # This will be mapped to the User id in create_sample_user_state
        data=dict(
            user_regions=[
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
                R.prop(
                    'data',
                    user_state_dict
                )
            )
        )
    )
    # Save the user_state with the complete data
    user_state = UserState(**user_state_values)
    user_state.save()
    return user_state


def form_sample_user_state_data(regions, data):
    """
    Given data in the form dict(region_keys=[...], ...), converts region_keys to
    regions=[{id:x}, {id:y}, ...] by resolving the regions
    :param regions: Persisted regions
    :param {dict} data: Sample data in the form:
    dict(
        user_regions=[
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
    :return: Data in the form dict(user_regions=[dict(region=dict(id=x), mapbox=..., ...), ...])
    """
    regions_by_key = R.map_prop_value_as_index('key', regions)
    return R.merge(
        # Rest of data that's not regions
        R.omit(['user_regions'], data),
        dict(user_regions=R.map(
            # Find the id of th region that matches,
            # returning dict(id=region_id). We can't return the whole region
            # because we are saving within json data, not the Django ORM
            lambda user_region: R.merge(
                # Other stuff like mapbox
                R.omit(['region'], user_region),
                # Replace key with id
                dict(
                    region=dict(
                        # Resolve the persisted Region by key
                        id=R.compose(
                            # third get the id
                            R.prop('id'),
                            # second resolve the region
                            lambda k: R.prop(k, regions_by_key),
                            # first get the key
                            R.item_str_path('region.key')
                        )(user_region)
                    )
                )
            ),
            R.prop('user_regions', data)
        ))
    )


def create_sample_user_states():
    """
        Creates sample persisted users that contain references to persisted regions
    :return:
    """
    users = create_sample_users()
    # Create regions for the users to associate with. A region also needs and owner so we pass users to the function
    regions = create_sample_regions(users)

    # Convert all sample user_state dicts to persisted UserState instances
    # Use the username to match a real user
    user_states = R.map(
        lambda sample_user_state: create_sample_user_state(regions, sample_user_state),

        sample_user_states
    )
    return user_states
