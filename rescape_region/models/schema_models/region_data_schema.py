from rescape_python_helpers import ramda as R
from graphene import ObjectType, String, Float, List, Field, Int

###
region_data_fields = dict(
    example=dict(type=Float)
)

RegionDataType = type(
    'RegionDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        region_data_fields)
)
