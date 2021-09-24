from rescape_python_helpers import ramda as R
from django.db import transaction

from rescape_region.models import SearchJurisdiction

local_sample_locations = [
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


def create_local_sample_locations(cls, sample_locations=local_sample_locations):
    """
        Create sample locations
    :param cls: THe Location class
    :param sample_locations Defaults to _sample_locations defined in this file. Apps using this can pass their own
    :return:
    """
    delete_sample_locations(cls)
    # Convert all sample location dicts to persisted Location instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_location(cls, kv[1]),
        enumerate(sample_locations)
    )

def create_sample_search_location(cls, search_location_dict):
    """
        Matches the location name with street.name of a new search location

    :param cls:
    :param search_location_dict:
    :return:
    """

    search_location = cls(
        name=f"Searchin' for {search_location_dict.name}",
        street=dict(nameContains=search_location_dict.name)
    )
    search_location.save()
    search_jurisdictions = R.map(lambda instance: instance.save() or instance, [SearchJurisdiction(data=dict(country='Nowhere'))])
    search_location.jurisdictions.set(*search_jurisdictions)
    return search_location

def delete_sample_search_locations(cls):
    cls.objects.all().delete()


def create_local_sample_search_locations(cls, sample_locations):
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
