from graphene import ObjectType, Float, List, Field, Int, Boolean
from rescape_graphene import resolver_for_dict_field, \
    resolver_for_dict_list, model_resolver_for_dict_field, type_modify_fields, FeatureCollectionDataType
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R

from rescape_region.schema_models.mapbox.mapbox_data_schema import MapboxDataType, mapbox_data_fields

activity_data_fields = dict(
    isActive=dict(type=Boolean)
)

ActivityDataType = type(
    'ActivityDataType',
    (ObjectType,),
    type_modify_fields(activity_data_fields)
)


def user_global_data_fields(class_config):
    return dict(
        # The mapbox state for the user's Global settings
        mapbox=dict(
            type=MapboxDataType,
            graphene_type=MapboxDataType,
            fields=mapbox_data_fields,
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
        )
    )


# References the Global instance, dictating settings imposed on or chosen by a user globally
# to which they have some level of access. This also adds settings like mapbox that are particular to the User's use
# of the Region but that the Region itself doesn't care about
def UserGlobalDataType(class_config):
    return type(
        'UserGlobalDataType',
        (ObjectType,),
        type_modify_fields(user_global_data_fields(class_config))
    )


def user_search_field_for_user_state_scopes(user_search_graphene_class, user_search_graphene_fields):
    """
        user_searches is a list of dicts specific to the application
        for instance each user_search type might contain fields of the
        type django LocationSearch, RegionSearch, ProductSearch, which are models that
        correspond to Location, Region, Product, but include filter properties.
        It might be possible to generalize this here, and assume that every user_search
        needs a config LocationSearch/Location, RegionSearch/Region, ProductSearch/Product
        and corresponding graphene types. For now we'll just require a
        user_searches_graphene_class that can point to all the application specific types via fields
        :param user_search_graphene_class The graphene class that contains to application specific
        fields
        :param user_search_graphene_fields The graphene fields of the user_search_graphene_class
        :return:
    """
    return dict(
        type=user_search_graphene_class,
        graphene_type=user_search_graphene_class,
        fields=user_search_graphene_fields,
        type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
    )


def user_region_data_fields(class_config):
    region_class_config = R.prop('region', class_config)
    additional_user_scope_schemas = R.prop('additional_user_scope_schemas', class_config)\
        if R.prop_or(None, 'additional_user_scope_schemas', class_config) else {}

    return dict(
        # References a Region.
        region=dict(
            type=R.prop('graphene_class', region_class_config),
            graphene_type=R.prop('graphene_class', region_class_config),
            fields=R.prop('graphene_fields', region_class_config),
            type_modifier=lambda *type_and_args: Field(
                *type_and_args,
                resolver=model_resolver_for_dict_field(R.prop('model_class', region_class_config))
            )
        ),
        # The mapbox state for the user's use of this Region
        mapbox=dict(
            type=MapboxDataType,
            graphene_type=MapboxDataType,
            fields=mapbox_data_fields,
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
        ),
        # Is this region the active region for this user
        activity=dict(
            type=ActivityDataType,
            graphene_type=ActivityDataType,
            fields=activity_data_fields,
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
        ),
        # A list of user_searches that reference application specific classes
        userSearch=user_search_field_for_user_state_scopes(
            *R.props(['graphene_class', 'graphene_fields'], R.prop('user_search', class_config))
        ),
        **additional_user_scope_schemas
    )


# References a Region model instance, dictating settings imposed on or chosen by a user for a particular Region
# to which they have some level of access. This also adds settings like mapbox that are particular to the User's use
# of the Region but that the Region itself doesn't care about
def UserRegionDataType(class_config):
    return type(
        'UserRegionDataType',
        (ObjectType,),
        type_modify_fields(user_region_data_fields(class_config))
    )


def user_project_data_fields(class_config):
    project_class_config = R.prop('project', class_config)
    location_class_config = R.prop('location', class_config)
    additional_user_scope_schemas = R.prop('additional_user_scope_schemas', class_config)\
        if R.prop_or(None, 'additional_user_scope_schemas', class_config) else {}

    return dict(
        # References a Project
        project=dict(
            type=R.prop('graphene_class', project_class_config),
            graphene_type=R.prop('graphene_class', project_class_config),
            fields=R.prop('graphene_fields', project_class_config),
            type_modifier=lambda *type_and_args: Field(
                *type_and_args,
                resolver=model_resolver_for_dict_field(R.prop('model_class', project_class_config))
            )
        ),
        # The mapbox state for the user's use of this Project
        mapbox=dict(
            type=MapboxDataType,
            graphene_type=MapboxDataType,
            fields=mapbox_data_fields,
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
        ),
        locations=dict(
            type=R.prop('graphene_class', location_class_config),
            graphene_type=R.prop('graphene_class', location_class_config),
            fields=R.prop('graphene_fields', location_class_config),
            type_modifier=lambda *type_and_args: List(*type_and_args)
        ),
        # Is the project active for the user and similar
        activity=dict(
            type=ActivityDataType,
            graphene_type=ActivityDataType,
            fields=activity_data_fields,
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
        ),
        # A list of user_searches that reference application specific classes
        userSearch=user_search_field_for_user_state_scopes(
            *R.props(['graphene_class', 'graphene_fields'], R.prop('user_search', class_config))
        ),
        **additional_user_scope_schemas
    )


# References a Project model instance, dictating settings imposed on or chosen by a user for a particular Project
# to which they have some level of access. This also adds settings like mapbox that are particular to the User's use
# of the Project but that the Project itself doesn't care about
def UserProjectDataType(class_config):
    return type(
        'UserProjectDataType',
        (ObjectType,),
        type_modify_fields(user_project_data_fields(class_config))
    )


# User State for their use of Regions, Projects, etc
def user_state_data_fields(class_config):


    return dict(
        userGlobal=dict(
            type=UserGlobalDataType(class_config),
            graphene_type=UserGlobalDataType(class_config),
            fields=user_global_data_fields(class_config),
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field)
        ),
        userRegions=dict(
            type=UserRegionDataType(class_config),
            graphene_type=UserRegionDataType(class_config),
            fields=user_region_data_fields(class_config),
            type_modifier=lambda *type_and_args: List(*type_and_args, resolver=resolver_for_dict_list)
        ),
        userProjects=dict(
            type=UserProjectDataType(class_config),
            graphene_type=UserProjectDataType(class_config),
            fields=user_project_data_fields(class_config),
            type_modifier=lambda *type_and_args: List(*type_and_args, resolver=resolver_for_dict_list)
        )

    )


def UserStateDataType(class_config):
    return type(
        'UserStateDataType',
        (ObjectType,),
        type_modify_fields(user_state_data_fields(class_config))
    )
