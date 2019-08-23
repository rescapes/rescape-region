from rescape_graphene import resolver_for_dict_field, type_modify_fields
from graphene import ObjectType, String, Float, List, Field, Int


# Params used to limit what locations are available to the Region
from rescape_region.schema_models.location_data_schema import LocationDataType, location_data_fields
from rescape_region.schema_models.user_state_data_schema import MapboxDataType, mapbox_data_fields


region_data_fields = dict(
    # This is a singular object with a params field used to resolve locations
    locations=dict(
        type=LocationDataType,
        graphene_type=LocationDataType,
        fields=location_data_fields,
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
