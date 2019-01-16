import graphene
from graphene.types.generic import GenericScalar
from rescape_graphene import resolver_for_dict_field, type_modify_fields
from graphene import ObjectType, Field, Float

location_data_fields = dict(
    example=dict(type=Float)
)

LocationDataType = type(
    'LocationDataType',
    (ObjectType,),
    type_modify_fields(location_data_fields)
)
