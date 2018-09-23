from rescape_python_helpers import ewkt_from_feature
from rescape_python_helpers.geospatial.geometry_helpers import ewkt_from_feature_collection


def feature_geometry_default():
    """
    The default geometry is a polygon of the earth's extent
    :return:
    """
    return ewkt_from_feature(
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon", "coordinates": [[[-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180]]]
            }
        }
    )


def feature_collection_geometry_default():
    """
        Default FeatureCollection as ewkt representing the entire world
    :return:
    """
    return ewkt_from_feature_collection(
        {
            'type': 'FeatureCollection',
            'features': [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon", "coordinates": [[[-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180]]]
                }
            }]
        }
    )


def region_default():
    return dict()


def user_state_default():
    return dict()


def group_state_default():
    return dict()
