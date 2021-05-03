from graphene import ObjectType, String
from rescape_graphene import type_modify_fields

# TODO right now every location just has one jurisdiction object that corresponds
# to the original location jurisdiction properties.
# In the future this will look more like OSM or Google's jurisdictions, where
# a locaiton has a list of them starting at country and working down to more specific levels
jurisdiction_data_fields = dict(
    country=dict(type=String),
    state=dict(type=String),
    city=dict(type=String),
    county=dict(type=String),
    borough=dict(type=String),
    district=dict(type=String),
    neighborhood=dict(type=String)
)

JurisdictionDataType = type(
    'JurisdictionDataType',
    (ObjectType,),
    type_modify_fields(jurisdiction_data_fields)
)
