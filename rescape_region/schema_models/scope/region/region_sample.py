from rescape_python_helpers import ramda as R
from django.db import transaction

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
def create_sample_region(cls, region_dict):
    # Save the region with the complete data

    region = cls(**region_dict)
    region.save()
    return region


def delete_sample_regions(cls):
    cls.objects.all().delete()


def create_sample_regions(cls):
    """
        Create sample regions
    :param cls The Region class
    :return:
    """
    delete_sample_regions(cls)
    # Convert all sample region dicts to persisted Region instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_region(cls, kv[1]),
        enumerate(sample_regions)
    )
