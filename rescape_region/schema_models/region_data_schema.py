from graphene.types.generic import GenericScalar
from rescape_graphene import resolver_for_dict_field
from rescape_python_helpers import ramda as R
from graphene import ObjectType, String, Float, List, Field, Int


region_location_data_fields = dict(
    # References a Region.
    # For simplicity we limit fields to id. Mutations can only use id, and a query doesn't need other
    # details of the region--it can query separately for that. We could offer all fields in a query only
    # version of these fields
    params=dict(
        type=GenericScalar,
        graphene_type=GenericScalar,
    ),
)

# References a Region location,
RegionLocationDataType = type(
    'RegionLocationDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        region_location_data_fields)
)

region_data_fields = dict(
    # This is a singular object with a params field used to resolve locations
    locations=dict(
        type=RegionLocationDataType,
        graphene_type=RegionLocationDataType,
        fields=region_location_data_fields,
        type_modifier=lambda typ: Field(typ, resolver=resolver_for_dict_field)
    )
)

RegionDataType = type(
    'RegionDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        region_data_fields)
)
