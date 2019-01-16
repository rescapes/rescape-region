from graphene.types.generic import GenericScalar
from rescape_graphene import resolver_for_dict_field, type_modify_fields
from rescape_python_helpers import ramda as R
from graphene import ObjectType, String, Float, List, Field, Int

project_data_fields = dict(
    example=dict(type=Float)
)

ProjectDataType = type(
    'ProjectDataType',
    (ObjectType,),
    type_modify_fields(project_data_fields)
)
