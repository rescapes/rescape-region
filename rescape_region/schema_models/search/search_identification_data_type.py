from graphene import ObjectType, String, Int
from rescape_graphene import type_modify_fields
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields, READ

search_identification_fields = dict(id=dict(type=Int))
# Stores the id to search for. For example if this is used by SearchLocationType, instances
# of SearchLocationDataType will have a property identification=dict(id=242424, idContains=[3424, 2242], etc.)
search_identification_data_fields = fields_with_filter_fields(
    search_identification_fields,
    'SearchIdentificationDataType',
    crud=READ
)

SearchIdentificationDataType = type(
    'SearchIdentificationDataType',
    (ObjectType,),
    type_modify_fields(search_identification_fields)
)
