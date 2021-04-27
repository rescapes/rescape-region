from graphene import ObjectType, Int
from rescape_graphene.graphql_helpers.schema_helpers import fields_with_filter_fields

search_identification_fields = dict(id=dict(type=Int))

SearchIdentificationDataType = type(
    'SearchIdentificationDataType',
    (ObjectType,),
    fields_with_filter_fields(
        search_identification_fields,
        'SearchIdentificationDataType',
        create_filter_fields_for_mutations=True
    )
)
