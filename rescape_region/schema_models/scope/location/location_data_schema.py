from graphene.types.generic import GenericScalar
from rescape_graphene import type_modify_fields
from graphene import ObjectType

location_data_fields = dict(
    example=dict(
        type=GenericScalar,
        graphene_type=GenericScalar,
    )
)

LocationDataType = type(
    'LocationDataType',
    (ObjectType,),
    type_modify_fields(location_data_fields)
)
