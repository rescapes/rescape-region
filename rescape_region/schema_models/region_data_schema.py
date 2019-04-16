from graphene.types.generic import GenericScalar
from rescape_graphene import resolver_for_dict_field, type_modify_fields
from graphene import ObjectType, String, Float, List, Field, Int


# Params used to limit what locations are available to the Region
region_location_data_fields = dict(
    params=dict(
        type=GenericScalar,
        graphene_type=GenericScalar,
    ),
)

# References a RegionLocation
RegionLocationDataType = type(
    'RegionLocationDataType',
    (ObjectType,),
    type_modify_fields(region_location_data_fields)
)

region_data_fields = dict(
    # This is a singular object with a params field used to resolve locations
    locations=dict(
        type=RegionLocationDataType,
        graphene_type=RegionLocationDataType,
        fields=region_location_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    )
)

RegionDataType = type(
    'RegionDataType',
    (ObjectType,),
    type_modify_fields(region_data_fields)
)
