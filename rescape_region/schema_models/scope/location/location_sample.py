from rescape_python_helpers import ramda as R
from django.db import transaction

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
def create_sample_location(cls, location_dict):
    # Save the location with the complete data

    location = cls(**location_dict)
    location.save()
    return location


def delete_sample_locations(cls):
    cls.objects.all().delete()


def create_sample_locations(cls):
    """
        Create sample locations
    :param cls: THe Location class
    :return:
    """
    delete_sample_locations(cls)
    # Convert all sample location dicts to persisted Location instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_location(cls, kv[1]),
        enumerate(sample_locations)
    )

def create_sample_search_location(cls, sample_location):
    """
        Matches the location name with street.name of a new search location

    :param cls:
    :param sample_location:
    :return:
    """

    search_location = cls(street=dict(nameContains=sample_location.name))
    search_location.save()
    return search_location

def delete_sample_search_locations(cls):
    cls.objects.all().delete()


def create_sample_search_locations(cls, sample_locations):
    """
        Create a sample search location that matches each location by name
    :param cls:
    :param sample_locations:
    :return:
    """
    delete_sample_search_locations(cls)
    return R.map(
        lambda kv: create_sample_search_location(cls, kv[1]),
        enumerate(sample_locations)
    )
