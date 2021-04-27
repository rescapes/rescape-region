from rescape_python_helpers import ramda as R
from django.db import transaction

sample_settings = [
    dict(
        key='global',
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
                #mapboxApiAccessToken='pk.eyJ1IjoiY2Fsb2NhbiIsImEiOiJjaXl1aXkxZjkwMG15MndxbmkxMHczNG50In0.07Zu3XXYijL6GJMuxFtvQg',
                viewport={},
            )
        )
    )
]


@transaction.atomic
def create_sample_settings(cls, settings_dict):
    # Save the settings with the complete data

    settings = cls(**settings_dict)
    settings.save()
    return settings


def delete_sample_settings(cls):
    cls.objects.all().delete()


def create_sample_settings_sets(cls):
    """
        Create sample settings
    :param cls The Settings class
    :return:
    """
    delete_sample_settings(cls)
    # Convert all sample settings dicts to persisted Settings instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_settings(cls, kv[1]),
        enumerate(sample_settings)
    )
