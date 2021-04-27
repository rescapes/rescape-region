from graphene import ObjectType
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields

from rescape_region.schema_models.scope.location.location_data_schema import location_data_fields

search_location_data_fields = fields_with_filter_fields(
    location_data_fields, 'SearchLocationDataType',
    create_filter_fields_for_mutations=True)

SearchLocationDataType = type(
    'SearchLocationDataType',
    (ObjectType,),
    location_data_fields
)
