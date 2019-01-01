from rescape_python_helpers import ramda as R
from django.db import transaction

from rescape_region.models.region import Region

sample_regions = [
    dict(
        key='belgium',
        name='Belgium',
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
def create_sample_region(region_dict):
    # Save the region with the complete data

    region = Region(**region_dict)
    region.save()
    return region


def delete_sample_regions():
    Region.objects.all().delete()


def create_sample_regions():
    """
        Create sample regions
    :param users:
    :return:
    """
    delete_sample_regions()
    # Convert all sample region dicts to persisted Region instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_region(kv[1]),
        enumerate(sample_regions)
    )
