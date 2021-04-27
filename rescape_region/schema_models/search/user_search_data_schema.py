from graphene import ObjectType, List
from rescape_graphene import resolver_for_dict_list
# Params used to limit what locations are available to the Region
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields

from rescape_region.schema_models.scope.location.location_data_schema import location_data_fields
from rescape_region.schema_models.search.user_search_location_data_schema import UserSearchLocationDataType

# The sample user search data fields for rescape-region. This must be overridden in applications
# that use rescape-region
user_search_data_fields = dict(
    user_search_locations=dict(
        type=UserSearchLocationDataType,
        graphene_type=UserSearchLocationDataType,
        # Search fields are added to location_data_fields
        fields=location_data_fields,
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
    fields_with_filter_fields(
        user_search_data_fields,
        'UserSearchDataType',
        create_filter_fields_for_mutations=True
    )
)

# This must be referenced in settings.py at USER_SEARCH_DATA_SCHEMA_CONFIG
user_search_data_schema_config = dict(
    graphene_class=UserSearchDataType,
    graphene_fields=user_search_data_fields
)
