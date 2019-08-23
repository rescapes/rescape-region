from graphene.types.generic import GenericScalar
from rescape_graphene import type_modify_fields
from graphene import ObjectType

location_data_fields = dict(
    params=dict(
        type=GenericScalar,
        graphene_type=GenericScalar,
    ),
)

# References a RegionLocation
LocationDataType = type(
    'RegionsLocationDataType',
    (ObjectType,),
    type_modify_fields(location_data_fields)
)
