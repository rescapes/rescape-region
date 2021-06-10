from graphene import Float, Int, ObjectType, Field
from rescape_graphene import FeatureCollectionDataType, resolver_for_dict_field, type_modify_fields
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields

viewport_data_fields = dict(
    latitude=dict(type=Float),
    longitude=dict(type=Float),
    zoom=dict(type=Int),
    # Overrides latitude, longitude, and zoom to support more complex types
    extent=dict(
        type=FeatureCollectionDataType,
        graphene_type=FeatureCollectionDataType,
        fields=feature_collection_data_type_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    )
)

# Viewport settings within Mapbox
ViewportDataType = type(
    'ViewportDataType',
    (ObjectType,),
    type_modify_fields(viewport_data_fields)
)

mapbox_data_fields = dict(
    viewport=dict(
        type=ViewportDataType,
        graphene_type=ViewportDataType,
        fields=viewport_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    )
)

# Mapbox settings for the User's use of a particular Region
MapboxDataType = type(
    'MapboxDataType',
    (ObjectType,),
    type_modify_fields(mapbox_data_fields)
)
