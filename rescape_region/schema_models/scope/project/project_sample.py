from rescape_python_helpers import ramda as R
from django.db import transaction


def sample_projects(users):
    return [
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
            data=dict(),
            user=users[0]
        )
    ]


@transaction.atomic
def create_sample_project(cls, region, project_dict):
    # Save the project with the complete data

    project = cls(region=region, **project_dict)
    project.save()
    return project


def delete_sample_projects(cls):
    cls.objects.all().delete()


def create_sample_projects(cls, users, regions):
    """
        Create sample projects
    :param cls: The Project class
    :param users: Users to own the projects
    :param regions: Assign a region to each project
    :return:
    """
    delete_sample_projects(cls)
    # Convert all sample project dicts to persisted Project instances
    # Give each reach an owner
    return R.map(
        lambda kv: create_sample_project(cls, regions[R.modulo(kv[0], R.length(regions))], kv[1]),
        enumerate(sample_projects(users))
    )
