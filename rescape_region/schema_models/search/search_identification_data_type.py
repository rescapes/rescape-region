from graphene import ObjectType, Int
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields, type_modify_fields

_search_identification_fields = dict(id=dict(type=Int))
search_identification_fields = fields_with_filter_fields(
    _search_identification_fields,
    'SearchIdentificationDataType',
    create_filter_fields_for_search_type=True
)

SearchIdentificationDataType = type(
    'SearchIdentificationDataType',
    (ObjectType,),
    type_modify_fields(search_identification_fields)
)
