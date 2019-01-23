from rescape_python_helpers import ramda as R
from django.db import transaction

from rescape_region.models import Location

sample_locations = [
    dict(
        key='grandPlace',
        name='Grand Place',
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
    dict(
        key='petitPlace',
        name='Petit Place',
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
]


@transaction.atomic
def create_sample_location(location_dict):
    # Save the location with the complete data

    location = Location(**location_dict)
    location.save()
    return location


def delete_sample_locations():
    Location.objects.all().delete()


def create_sample_locations():
    """
        Create sample locations
    :param users:
    :return:
    """
    delete_sample_locations()
    # Convert all sample location dicts to persisted Location instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_location(kv[1]),
        enumerate(sample_locations)
    )
