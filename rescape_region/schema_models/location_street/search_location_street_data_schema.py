from graphene import ObjectType
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields, type_modify_fields

from rescape_region.schema_models.location_street.location_street_data_schema import location_street_data_fields

search_location_street_data_fields = fields_with_filter_fields(
    location_street_data_fields,
    'SearchLocationStreetDataType',
    create_filter_fields_for_search_type=True
)

SearchLocationStreetDataType = type(
    'SearchLocationStreetSopDataType',
    (ObjectType,),
    type_modify_fields(search_location_street_data_fields)
)
