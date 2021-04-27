from graphene import ObjectType, Field
from rescape_graphene import resolver_for_dict_field, type_modify_fields

# Params used to limit what locations are available to the Region
from rescape_region.schema_models.scope.location.location_params_data_schema import location_params_data_fields, LocationParamsDataType
from rescape_region.schema_models.user_state.user_state_data_schema import MapboxDataType, mapbox_data_fields

region_data_fields = dict(
    # This is a singular object with a params field used to resolve locations
    locations=dict(
        type=LocationParamsDataType,
        graphene_type=LocationParamsDataType,
        fields=location_params_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    ),
    # The default mapbox settings for the region
    mapbox=dict(
        type=MapboxDataType,
        graphene_type=MapboxDataType,
        fields=mapbox_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    ),
)

RegionDataType = type(
    'RegionDataType',
    (ObjectType,),
    type_modify_fields(region_data_fields)
)
