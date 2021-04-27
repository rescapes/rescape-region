from rescape_python_helpers import ramda as R
from rescape_graphene import resolver_for_dict_list, type_modify_fields
from graphene import ObjectType, List


def group_state_data_fields(class_config):
    return dict(
        group_regions=dict(
            # Intentional use of UserRegionDataType here. We want any group state to match user state
            type=R.item_str_path('region.graphene_class', class_config),
            graphene_type=R.item_str_path('region.graphene_class', class_config),
            fields=R.item_str_path('region.graphene_fields', class_config),
            type_modifier=lambda *type_and_args: List(*type_and_args, resolver=resolver_for_dict_list)
        )
    )


def GroupStateDataType(class_config):
    return type(
        'GroupStateDataType',
        (ObjectType,),
        type_modify_fields(group_state_data_fields(class_config))
    )
