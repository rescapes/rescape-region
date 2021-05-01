from graphene import ObjectType, Field
from rescape_graphene import resolver_for_dict_field, model_resolver_for_dict_field, type_modify_fields

from rescape_region.models.search_location import SearchLocation
from rescape_region.schema_models.search.search_location_schema import search_location_fields, SearchLocationType
from rescape_region.schema_models.user_state.user_state_data_schema import ActivityDataType, \
    activity_data_fields

# Params used to limit what locations are available to the Region


# We don't add filter fields at this level. The filter fields start at search_location.data, search_location.geojson,
# etc. We don't want a search_location.dataContains field as part of the SearchLocationType class


# The sample user search data fields for rescape-region. This must be overridden in applications
# that use rescape-region
user_search_location_data_fields = dict(
    searchLocation=dict(
        type=SearchLocationType,
        graphene_type=SearchLocationType,
        fields=search_location_fields,
        # References the model class
        type_modifier=lambda *type_and_args: Field(
            *type_and_args,
            resolver=model_resolver_for_dict_field(SearchLocation)
        )
    ),
    # Indicates if this SearchLocation is active for the user
    activity=dict(
        type=ActivityDataType,
        graphene_type=ActivityDataType,
        fields=activity_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    )
)

UserSearchLocationDataType = type(
    'UserSearchLocationDataType',
    (ObjectType,),
    type_modify_fields(user_search_location_data_fields),
)
