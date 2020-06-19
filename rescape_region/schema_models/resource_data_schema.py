from rescape_python_helpers import ramda as R
from rescape_graphene import resolver_for_dict_field, resolver_for_dict_list
from graphene import ObjectType, String, Float, List, Field, Int, Boolean

stage_data_fields = dict(
    key=dict(type=String),
    name=dict(type=String),
    targets=dict(type=String, type_modifier=lambda typ: List(typ))
)

StageDataType = type(
    'StageDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        stage_data_fields)
)

resource_settings_data_fields = dict(
    defaultLocation=dict(type=Float, type_modifier=lambda typ: List(Float)),
    unit=dict(type=String),
    columns=dict(type=String, type_modifier=lambda typ: List(typ)),
    stageKey=dict(type=String),
    valueKey=dict(type=String),
    locationKey=dict(type=String),
    nodeNameKey=dict(type=String),
    nodeColorKey=dict(type=String),
    linkColorKey=dict(type=String),

    stages=dict(
        type=StageDataType,
        graphene_type=StageDataType,
        fields=stage_data_fields,
        type_modifier=lambda typ: List(typ, resolver=resolver_for_dict_list)
    )
)

ResourceSettingsDataType = type(
    'ResourceSettingsDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        resource_settings_data_fields)
)

geometry_data_fields = dict(
    type=dict(type=String),
    coordinates=dict(type=Float, type_modifier=lambda typ: List(typ))
)

GeometryDataType = type(
    'GeometryDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        geometry_data_fields)
)

node_data_fields = dict(
    name=dict(type=String),
    # Index is the number used by the links to identify the node in a set of nodes
    node_index=dict(type=Int),
    type=dict(type=String),
    value=dict(type=Float),
    # TODO this should be a rescape_region FeatureCollection type to hold full geojson
    geometry=dict(
        type=GeometryDataType,
        graphene_type=GeometryDataType,
        fields=geometry_data_fields,
        type_modifier=lambda typ: Field(typ, resolver=resolver_for_dict_field),
    ),
    properties=dict(type=String, type_modifier=lambda typ: List(typ)),
    propertyValues=dict(type=String, type_modifier=lambda typ: List(typ)),
    coordinates=dict(type=Float),
    isGeneralized=dict(type=Boolean),
)

NodeDataType = type(
    'NodeDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        node_data_fields)
)

link_data_fields = dict(
    value=dict(type=Float),
    source=dict(type=Int),
    target=dict(type=Int),
)

LinkDataType = type(
    'LinkDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        link_data_fields)
)

graph_data_fields = dict(
    links=dict(type=LinkDataType, graphene_type=LinkDataType, fields=link_data_fields, type_modifier=lambda typ: List(typ, resolver=resolver_for_dict_list)),
    nodes=dict(type=NodeDataType, graphene_type=NodeDataType, fields=node_data_fields, type_modifier=lambda typ: List(typ, resolver=resolver_for_dict_list))
)

GraphDataType = type(
    'GraphDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        graph_data_fields)
)

resource_data_fields = dict(
    settings=dict(
        type=ResourceSettingsDataType,
        graphene_type=ResourceSettingsDataType,
        fields=resource_settings_data_fields,
        type_modifier=lambda typ: Field(typ, resolver=resolver_for_dict_field)
    ),
    rawData=dict(
        type=String,
        type_modifier=lambda typ: List(typ)
    ),
    graph=dict(
        type=GraphDataType,
        graphene_type=GraphDataType,
        fields=graph_data_fields,
        type_modifier=lambda typ: Field(typ, resolver=resolver_for_dict_field)
    ),
    material=dict(type=String)
)

ResourceDataType = type(
    'ResourceDataType',
    (ObjectType,),
    R.map_with_obj(
        # If we have a type_modifier function, pass the type to it, otherwise simply construct the type
        lambda k, v: R.prop_or(lambda typ: typ(), 'type_modifier', v)(R.prop('type', v)),
        resource_data_fields)
)
