from graphene import ObjectType, Int
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields, type_modify_fields

from rescape_region.schema_models.jurisdiction.jurisdiction_data_schema import jurisdiction_data_fields

search_jurisdiction_data_fields = fields_with_filter_fields(
    jurisdiction_data_fields,
    'SearchJurisdictionDataType',
    create_filter_fields_for_search_type=True
)

SearchJurisdictionDataType = type(
    'SearchJurisdictionDataType',
    (ObjectType,),
    type_modify_fields(search_jurisdiction_data_fields)
)
