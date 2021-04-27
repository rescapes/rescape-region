from graphene import ObjectType
from rescape_graphene import type_modify_fields
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields, READ
from rescape_region.schema_models.location_data_schema import location_data_fields

search_location_data_fields = fields_with_filter_fields(location_data_fields, 'SearchLocationDataType', crud=READ)
SearchLocationDataType = type(
    'SearchLocationDataType',
    (ObjectType,),
    type_modify_fields(location_data_fields)
)
