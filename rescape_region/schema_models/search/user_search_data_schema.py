from graphene import ObjectType, List
from rescape_graphene import resolver_for_dict_list
# Params used to limit what locations are available to the Region
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields, \
    top_level_allowed_filter_arguments, type_modify_fields

from rescape_region.schema_models.search.user_search_location_data_schema import UserSearchLocationDataType, \
    user_search_location_data_fields

# The sample user search data fields for rescape-region. This must be overridden in applications
# that use rescape-region
user_search_data_fields = dict(
    userSearchLocations=dict(
        type=UserSearchLocationDataType,
        graphene_type=UserSearchLocationDataType,
        # Search fields are added to location_data_fields
        fields=user_search_location_data_fields,
        # References the model class
        type_modifier=lambda *type_and_args: List(
            *type_and_args,
            resolver=resolver_for_dict_list
        )
    )
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
    graphene_fields=user_search_data_fields
)
