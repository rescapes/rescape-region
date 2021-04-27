from graphene import ObjectType, Float, Field, Int, String
from rescape_graphene import resolver_for_dict_field, \
    type_modify_fields

settings_viewport_data_fields = dict(
    latitude=dict(type=Float),
    longitude=dict(type=Float),
    zoom=dict(type=Int)
)

# Viewport settings within Mapbox
SettingsViewportDataType = type(
    'SettingsViewportDataType',
    (ObjectType,),
    type_modify_fields(settings_viewport_data_fields)
)

settings_mapbox_data_fields = dict(
    viewport=dict(
        type=SettingsViewportDataType,
        graphene_type=SettingsViewportDataType,
        fields=settings_viewport_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    )
)

# Mapbox settings for the User's use of a particular Region
SettingsMapboxDataType = type(
    'SettingsMapboxDataType',
    (ObjectType,),
    type_modify_fields(settings_mapbox_data_fields)
)

settings_api_data_field = dict(
    protocol=dict(type=String),
    host=dict(type=String),
    port=dict(type=String),
    path=dict(type=String),
)

# The API settings
SettingsApiDataType = type(
    'SettingsApiDataType',
    (ObjectType,),
    type_modify_fields(settings_api_data_field)
)

settings_overpass_data_fields = dict(
    cellSize=dict(type=Int),
    sleepBetweenCalls=dict(type=Int),
)

# The Overpass (OpenStreetMap) API settings
SettingsOverpassDataType = type(
    'SettingsOverpassDataType',
    (ObjectType,),
    type_modify_fields(settings_overpass_data_fields)
)

# User State for their use of Regions, Projects, etc
settings_data_fields = dict(
    domain=dict(type=String),
    api=dict(
        type=SettingsApiDataType,
        graphene_type=SettingsApiDataType,
        fields=settings_api_data_field,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    ),
    overpass=dict(
        type=SettingsOverpassDataType,
        graphene_type=SettingsOverpassDataType,
        fields=settings_overpass_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    ),
    mapbox=dict(
        type=SettingsMapboxDataType,
        graphene_type=SettingsMapboxDataType,
        fields=settings_mapbox_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    )
)

SettingsDataType = type(
    'SettingsDataType',
    (ObjectType,),
    type_modify_fields(settings_data_fields)
)
