from rescape_graphene import resolver_for_dict_field, type_modify_fields, resolver_for_dict_list
from graphene import ObjectType, Field, List

from rescape_region.model_helpers import get_location_schema
from rescape_region.schema_models.user_state_data_schema import MapboxDataType, mapbox_data_fields

project_data_fields = dict(
    # This is a singular object with a params field used to resolve locations
    locations=dict(
        type=get_location_schema()['graphene_class'],
        graphene_type=get_location_schema()['graphene_class'],
        fields=get_location_schema()['graphene_fields'],
        type_modifier=lambda *type_and_args: List(*type_and_args)
    ),

    # The default mapbox settings for the region
    mapbox=dict(
        type=MapboxDataType,
        graphene_type=MapboxDataType,
        fields=mapbox_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    )
)

ProjectDataType = type(
    'ProjectDataType',
    (ObjectType,),
    type_modify_fields(project_data_fields)
)
