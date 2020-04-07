from graphene import ObjectType, Float
from rescape_graphene import type_modify_fields

region_location_data_fields = dict(
    example=dict(type=Float)
)

RegionLocationDataType = type(
    'RegionLocationDataType',
    (ObjectType,),
    type_modify_fields(region_location_data_fields)
)
