from rescape_python_helpers import ramda as R
from rescape_graphene import resolver_for_dict_list
from graphene import ObjectType, List

from rescape_region.models.schema_models.user_state_data_schema import UserRegionDataType, user_region_data_fields

group_state_data_fields = dict(
    group_regions=dict(
        type=UserRegionDataType,
        graphene_type=UserRegionDataType,
        fields=user_region_data_fields,
        type_modifier=lambda typ: List(typ, resolver=resolver_for_dict_list)
    )
)

GroupStateDataType = type(
    'GroupStateDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        group_state_data_fields)
)
