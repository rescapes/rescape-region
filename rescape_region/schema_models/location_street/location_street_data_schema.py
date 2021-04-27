from graphene import ObjectType, String
from rescape_graphene import type_modify_fields

# These will some day be used by the LocationType instead of the blockname field
# It allows us to put street names in different languages like OSM does and have other properties
# such as street suffix

location_street_data_fields = dict(
    name=dict(type=String),
)

LocationStreetDataType = type(
    'LocationStreetSopDataType',
    (ObjectType,),
    type_modify_fields(location_street_data_fields)
)
