from graphene import ObjectType, Float, List, Field, Int, Boolean
from rescape_graphene import resolver_for_dict_field, \
    resolver_for_dict_list, model_resolver_for_dict_field, type_modify_fields
from rescape_python_helpers import ramda as R

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

activity_data_fields = dict(
    is_active=dict(type=Boolean)
)

ActivityDataType = type(
    'ActivityDataType',
    (ObjectType,),
    type_modify_fields(activity_data_fields)
)


def user_global_data_fields(class_config):
    return {
        # The mapbox state for the user's Global settings
        'mapbox': dict(
            type=MapboxDataType,
            graphene_type=MapboxDataType,
            fields=mapbox_data_fields,
            type_modifier=lambda *type_and_args: Field(*type_and_args, resolver=resolver_for_dict_field),
        ),
    }


# References the Global instance, dictating settings imposed on or chosen by a user globally
# to which they have some level of access. This also adds settings like mapbox that are particular to the User's use
# of the Region but that the Region itself doesn't care about
def UserGlobalDataType(class_config):
    return type(
        'UserGlobalDataType',
        (ObjectType,),
        type_modify_fields(user_global_data_fields(class_config))
    )


def user_region_data_fields(class_config):
    region_class_config = R.prop('region', class_config)
    return dict(
        # References a Region.
        region=dict(
            type=R.prop('graphene_class', region_class_config),
            graphene_type=R.prop('graphene_class', region_class_config),
            fields=R.prop('graphene_fields', region_class_config),
            type_modifier=lambda *type_and_args: Field(
                *type_and_args,
                resolver=model_resolver_for_dict_field(R.prop('model_class', region_class_config)
                                                       )
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
        )
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
        )
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
