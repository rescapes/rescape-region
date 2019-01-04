from rescape_python_helpers import ramda as R
from rescape_graphene import resolver_for_dict_list, type_modify_fields
from graphene import ObjectType, List

from rescape_region.schema_models.user_state_data_schema import UserRegionDataType, user_region_data_fields

group_state_data_fields = dict(
    group_regions=dict(
        # Intentional use of UserRegionDataType here. We want any group state to match user state
        type=UserRegionDataType,
        graphene_type=UserRegionDataType,
        fields=user_region_data_fields,
        type_modifier=lambda *type_and_args: List(*type_and_args, resolver=resolver_for_dict_list)
    )
)

GroupStateDataType = type(
    'GroupStateDataType',
    (ObjectType,),
    type_modify_fields(group_state_data_fields)
)
