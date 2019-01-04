from rescape_python_helpers import ramda as R
from rescape_graphene import merge_with_django_properties, REQUIRE, resolver_for_dict_field, \
    resolver_for_dict_list, model_resolver_for_dict_field, type_modify_fields
from graphene import ObjectType, Float, List, Field, Int

from rescape_region.models import Region
from rescape_region.schema_models.region_schema import RegionType

viewport_data_fields = dict(
    latitude=dict(type=Float),
    longitude=dict(type=Float),
    zoom=dict(type=Int)
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

user_region_data_fields = dict(
    # References a Region.
    # For simplicity we limit fields to id. Mutations can only use id, and a query doesn't need other
    # details of the region--it can query separately for that. We could offer all fields in a query only
    # version of these fields
    region=dict(
        type=RegionType,
        graphene_type=RegionType,
        fields=merge_with_django_properties(RegionType, dict(id=dict(create=REQUIRE))),
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=model_resolver_for_dict_field(Region))
    ),
    # The mapbox state for the user's use of this Region
    mapbox=dict(
        type=MapboxDataType,
        graphene_type=MapboxDataType,
        fields=mapbox_data_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
    )
)

# References a Region model instance, dictating settings imposed on or chosen by a user for a particular Region
# to which they have some level of access. This also adds settings like mapbox that are particular to the User's use
# of the Region but that the Region itself doesn't care about
UserRegionDataType = type(
    'UserRegionDataType',
    (ObjectType,),
    type_modify_fields(user_region_data_fields)
)

user_state_data_fields = dict(
    userRegions=dict(
        type=UserRegionDataType,
        graphene_type=UserRegionDataType,
        fields=user_region_data_fields,
        type_modifier=lambda *type_and_args: List(*type_and_args, resolver=resolver_for_dict_list)
    )
)

UserStateDataType = type(
    'UserStateDataType',
    (ObjectType,),
    type_modify_fields(user_state_data_fields)
)
