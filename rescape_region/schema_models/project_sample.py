from rescape_python_helpers import ramda as R
from django.db import transaction

from rescape_region.models import Project

sample_projects = [
    dict(
        key='gare',
        name='Gare',
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
def create_sample_project(region, project_dict):
    # Save the project with the complete data

    project = Project(region=region, **project_dict)
    project.save()
    return project


def delete_sample_projects():
    Project.objects.all().delete()


def create_sample_projects(regions):
    """
        Create sample projects
    :param regions: Assign a region to each project
    :return:
    """
    delete_sample_projects()
    # Convert all sample project dicts to persisted Project instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_project(regions[R.modulo(kv[0], R.length(regions))], kv[1]),
        enumerate(sample_projects)
    )
