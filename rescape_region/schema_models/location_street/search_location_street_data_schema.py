from graphene import ObjectType
from rescape_graphene import READ
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields
from rescape_region.schema_models.location_street.location_street_data_schema import location_street_data_fields

search_location_street_data_fields = fields_with_filter_fields(
    location_street_data_fields,
    'SearchLocationStreetDataType',
    crud=READ
)

SearchLocationStreetDataType = type(
    'SearchLocationStreetSopDataType',
    (ObjectType,),
    search_location_street_data_fields
)
