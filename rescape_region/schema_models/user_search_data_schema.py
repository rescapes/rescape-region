from graphene import ObjectType, Field, List
from rescape_graphene import resolver_for_dict_field, type_modify_fields, resolver_for_dict_list, \
    model_resolver_for_dict_field

# Params used to limit what locations are available to the Region
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields

from rescape_region.models.search import Search
from rescape_region.schema_models.location_params_data_schema import location_params_data_fields, LocationParamsDataType
from rescape_region.schema_models.location_schema import location_fields
from rescape_region.schema_models.user_search_location_data_schema import UserSearchLocationDataType, \
    user_search_location_data_fields
from rescape_region.schema_models.user_state_data_schema import MapboxDataType, mapbox_data_fields, ActivityDataType, \
    activity_data_fields

search_fields = fields_with_filter_fields(
    location_fields,
    'SearchType'
)

SearchType = type(
    'SearchType',
    (ObjectType,),
    search_fields
)

# The sample user search data fields for rescape-region. This must be overridden in applications
# that use rescape-region
user_search_data_fields = dict(
    location_searches=dict(
        type=UserSearchLocationDataType,
        graphene_type=UserSearchLocationDataType,
        fields=user_search_location_data_fields,
        # References the model class
        type_modifier=lambda *type_and_args: List(
            *type_and_args,
            resolver=resolver_for_dict_list
        )
    ),
    # project_searches, etc here
)

UserSearchDataType = type(
    'UserSearchDataType',
    (ObjectType,),
    type_modify_fields(user_search_data_fields)
)

# This must be referenced in settings.py at USER_SEARCH_DATA_SCHEMA_CONFIG
user_search_data_schema_config = dict(
    graphene_class=UserSearchDataType,
    graphene_fields=UserSearchDataType
)
