from graphene.types.generic import GenericScalar
from rescape_graphene import type_modify_fields
from graphene import ObjectType

location_params_data_fields = dict(
    params=dict(
        type=GenericScalar,
        graphene_type=GenericScalar,
    ),
)

# References a get_location_schema()['model_class']
LocationParamsDataType = type(
    'LocationParamsDataType',
    (ObjectType,),
    type_modify_fields(location_params_data_fields)
)
