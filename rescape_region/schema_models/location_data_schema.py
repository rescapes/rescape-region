import graphene
from graphene.types.generic import GenericScalar
from rescape_graphene import resolver_for_dict_field, type_modify_fields
from graphene import ObjectType, Field, Float

region_location_data_fields = dict(
    example=dict(type=Float)
)

RegionLocationDataType = type(
    'RegionLocationDataType',
    (ObjectType,),
    type_modify_fields(region_location_data_fields)
)
