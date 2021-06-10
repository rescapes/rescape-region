import importlib

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rescape_python_helpers import ewkt_from_feature
from rescape_python_helpers.geospatial.geometry_helpers import ewkt_from_feature_collection
from rescape_python_helpers import ramda as R

def geos_feature_geometry_default():
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


def geos_feature_collection_geometry_default():
    """
        Default FeatureCollection as ewkt representing the entire world
    :return:
    """
    return ewkt_from_feature_collection(
        feature_collection_default()
    )


def feature_collection_default():
    return {
        'type': 'FeatureCollection',
        'features': [{
            "type": "Feature",
            "geometry": {
                "type": "Polygon", "coordinates": [[[-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180]]]
            }
        }]
    }


def region_data_default():
    return dict(locations=dict(params=[dict(
        country="ENTER A COUNTRY OR REMOVE THIS KEY/VALUE",
        state="ENTER A STATE/PROVINCE ABBREVIATION OR REMOVE THIS KEY/VALUE",
        city="ENTER A CITY OR REMOVE THIS KEY/VALUE",
        neighborhood="ENTER A NEIGHBORHOOD OR REMOVE THIS KEY/VALUE",
        blockname="ENTER A BLOCKNAME OR REMOVE THIS KEY/VALUE"
    )]))


def project_data_default():
    return dict()


def user_state_data_default():
    return dict(
        userRegions=[]
    )

def settings_data_default():
    return dict()

def group_state_data_default():
    return dict()

def get_region_model():
    """
    Uses the same technique as get_user_model() to get the current region model from settings
    :return:
    """
    try:
        return apps.get_model(settings.REGION_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("REGION_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "REGION_MODEL refers to model '%s' that has not been installed" % settings.REGION_MODEL
        )

def get_project_model():
    """
    Uses the same technique as get_user_model() to get the current project model from settings
    :return:
    """
    try:
        return apps.get_model(settings.PROJECT_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("PROJECT_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "PROJECT_USER_MODEL refers to model '%s' that has not been installed" % settings.PROJECT_MODEL
        )


def get_location_schema():
    """
    Uses the same technique as get_user_model() to get the current location model from settings
    :return:
    """
    try:
        modules = settings.LOCATION_SCHEMA_CONFIG.split('.')
        return getattr(
            importlib.import_module(R.join('.', R.init(modules))),
            R.last(modules)
        )
    except ValueError:
        raise ImproperlyConfigured('''settings.LOCATION_SCHEMA_CONFIG must point to the location schema config containing
    {
        model_class=Location,
        graphene_class=LocationType,
        graphene_fields=location_fields,
    }
''')
    except LookupError:
        raise ImproperlyConfigured(
            "settings.LOCATION_SCHEMA_CONFIG refers to model '%s' that has not been installed" % settings.LOCATION_SCHEMA_CONFIG
        )

def get_location_for_project_schema():
    """

    Like get_location_schema() but without reverse relationships that cause circular dependencies
    :return:
    """
    try:
        modules = settings.LOCATION_SCHEMA_FOR_PROJECT_CONFIG.split('.')
        return getattr(
            importlib.import_module(R.join('.', R.init(modules))),
            R.last(modules)
        )
    except ValueError:
        raise ImproperlyConfigured('''settings.LOCATION_SCHEMA_FOR_PROJECT_CONFIG must point to the location schema config containing
    {
        model_class=Location,
        graphene_class=LocationType,
        graphene_fields=location_fields,
    }
''')
    except LookupError:
        raise ImproperlyConfigured(
            "settings.LOCATION_SCHEMA_CONFIG refers to model '%s' that has not been installed" % settings.LOCATION_SCHEMA_CONFIG
        )

def get_user_search_data_schema():
    """
    Uses the same technique as get_user_model() to get the current location model from settings
    :return:
    """
    try:
        modules = settings.USER_SEARCH_DATA_SCHEMA_CONFIG.split('.')
        return getattr(
            importlib.import_module(R.join('.', R.init(modules))),
            R.last(modules)
        )
    except ValueError:
        raise ImproperlyConfigured('''settings.USER_SEARCH_DATA_SCHEMA_CONFIG must point to the user_search schema config containing
    {
        graphene_class=UserSearchType,
        graphene_fields=user_search_fields,
    }
''')
    except LookupError:
        raise ImproperlyConfigured(
            "settings.USER_SEARCH_DATA_SCHEMA_CONFIG refers to model '%s' that has not been installed" % settings.USER_SEARCH_DATA_SCHEMA_CONFIG
        )


def get_search_location_schema():
    """
    Uses the same technique as get_user_model() to get the current location model from settings
    :return:
    """
    try:
        modules = settings.SEARCH_LOCATION_SCHEMA_CONFIG.split('.')
        return getattr(
            importlib.import_module(R.join('.', R.init(modules))),
            R.last(modules)
        )
    except ValueError:
        raise ImproperlyConfigured('''settings.SEARCH_LOCATION_SCHEMA_CONFIG must point to the search_location schema config containing
    {
        model_class=SearchLocation,
        graphene_class=SearchLocationType,
        graphene_fields=search_location_fields,
    }
''')
    except LookupError:
        raise ImproperlyConfigured(
            "settings.SEARCH_LOCATION_SCHEMA_CONFIG refers to model '%s' that has not been installed" % settings.SEARCH_LOCATION_SCHEMA_CONFIG
        )
