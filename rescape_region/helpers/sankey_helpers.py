from rescape_python_helpers import ramda as R
import re
import locale


def string_to_float(flt):
    # https://stackoverflow.com/questions/9227335/parse-a-string-to-floats-with-different-separators
    # Remove anything not a digit, comma or period
    no_cruft = re.sub(r'[^\d,.-]', '', flt)

    # Split the result into parts consisting purely of digits
    parts = re.split(r'[,.]', no_cruft)

    # ...and sew them back together
    if len(parts) == 1:
        # No delimeters found
        flt = parts[0]
    elif len(parts[-1]) != 2:
        # >= 1 delimeters found. If the length of last part is not equal to 2, assume it is not a decimal part
        flt = ''.join(parts)
    else:
        flt = '%s%s%s' % (''.join(parts[0:-1]),
                          locale.localeconv()['decimal_point'],
                          parts[-1])

    # Convert to float. Invalid values are hopefully empty strings
    try:
        return float(flt) if flt != '' else float(0)
    except ValueError:
        raise ValueError("Something is wrong with the {1}. Can't convert it to a float".format(flt))


def stages_by_name(stages):
    return R.map_prop_value_as_index('name', stages)


def aberrate_location(index, location, factor=.005):
    """
       Minutely move locations so they don't overlap
    :param index: a counter to help with the aberration. Increment before calling each time
    :param location: Simple point location (two item array) of lat lon value
    :param factor: Sensitivity of aberration, defaults to .005
    :return:
    """
    return [coord + factor * (-index if index % 2 else index) * (i or -1) for coord, i in enumerate(location)]


def create_raw_nodes(resource):
    """
        Creates nodes for each column from the csv
    :param resource: The Resource object
    :return: Raw node data
    """
    columns = R.item_path(['data', 'settings', 'columns'], resource)
    raw_data = R.item_path(['data', 'rawData'], resource)
    return R.map(
        lambda line: R.from_pairs(
            zip(
                columns,
                line.split(';')
            )
        ),
        raw_data
    )


def resolve_location(default_location, coordinates, i):
    """
        Resolves the lat/lon based on the given coordinates string. If it is NA then default to BRUSSELS_LOCATION
    :param default_location: [lat, lon] representing the default location for coordinates marked 'NA'
    :param coordinates: comma separated lon/lat. We flip this since the software wants [lat, lon]
    :param i: Current index of coordinates, used for aberration
    :return: lat/lon array
    """
    if coordinates == 'NA':
        return dict(
            isGeneralized=True,
            location=aberrate_location(i, default_location)
        )
    else:
        return dict(
            isGeneralized=False,
            location=list(reversed(R.map(lambda coord: string_to_float(coord), coordinates.split(','))))
        )


def create_links(stages, value_key, nodes_by_stages):
    """
    Creates Sankey Links for the given ordered stages for the given nodes by stage
    :param [Object] stages Array of stage objects.
    :param {String} The value_key
    :param [Object] nodesByStages Keyed by stage key and valued by an array of nodes
    :return {*}
    """

    def process_stage(stage, i):
        # Get the current stage as the source if there are any in nodes_by_stage
        sources = R.prop_or(None, R.prop('key', stage), nodes_by_stages)
        if not sources:
            return []
        # Iterate through the stages until one with nodes is found
        target_stage = None
        try:
            target_stage = R.find(
                # Try to find nodes matching this potential target stage. There might not be any
                lambda stage: nodes_by_stages[R.prop('key', stage)] if R.has(R.prop('key', stage),
                                                                             nodes_by_stages) else None,
                stages[i + 1: R.length(stages)]
            )
        except ValueError:
            # It's coo, find errors if none is found. We really need R.first
            pass

        # If no more stages contain nodes, we're done
        if not target_stage:
            return []
        targets = nodes_by_stages[R.prop('key', target_stage)]

        def prop_lookup(node, prop):
            return R.prop(prop, dict(zip(node['properties'], node['propertyValues'])))

        # Create the link with the source_node and target_node. Later we'll add
        # in source and target that points to the nodes overall index in the graph,
        # but we don't want to compute the overall indices yet
        return R.chain(lambda source:
                       R.map(lambda target:
                             dict(
                                 source_node=source,
                                 target_node=target,
                                 value=string_to_float(prop_lookup(source, value_key))
                             ),
                             targets),
                       sources
                       )

    return R.flatten([process_stage(stage, i) for i, stage in enumerate(stages)])


def generate_sankey_data(resource):
    """
        Generates nodes and links for the given Resrouce object
    :param resource:  Resource object
    :return: A dict containing nodes and links. nodes are a dict key by stage name
        Results can be assigned to resource.data.sankey and saved
    """

    settings = R.item_path(['data', 'settings'], resource)
    stages = R.prop('stages', settings)
    stage_key = R.prop('stageKey', settings)
    value_key = R.prop('valueKey', settings)
    location_key = R.prop('locationKey', settings)
    node_name_key = R.prop('nodeNameKey', settings)
    default_location = R.prop('defaultLocation', settings)
    # A dct of stages by name
    stage_by_name = stages_by_name(stages)

    def accumulate_nodes(accum, raw_node, i):
        """
            Accumulate each node, keying by the name of the node's stage key
            Since nodes share stage keys these each result is an array of nodes
        :param accum:
        :param raw_node:
        :param i:
        :return:
        """
        location_obj = resolve_location(default_location, R.prop(location_key, raw_node), i)
        location = R.prop('location', location_obj)
        is_generalized = R.prop('isGeneralized', location_obj)
        # The key where then node is stored is the stage key
        key = R.prop('key', stage_by_name[raw_node[stage_key]])

        # Copy all properties from resource.data  except settings and raw_data
        # Also grab raw_node properties
        # This is for arbitrary properties defined in the data
        # We put them in properties and propertyValues since graphql hates arbitrary key/values
        properties = R.merge(
            R.omit(['settings', 'rawData'], R.prop('data', resource)),
            raw_node
        )
        return R.merge(
            # Omit accum[key] since we'll concat it with the new node
            R.omit([key], accum),
            {
                # concat accum[key] or [] with the new node
                key: R.concat(
                    R.prop_or([], key, accum),
                    # Note that the value is an array so we can combine nodes with the same stage key
                    [
                        dict(
                            value=string_to_float(R.prop(value_key, raw_node)),
                            type='Feature',
                            geometry=dict(
                                type='Point',
                                coordinates=location
                            ),
                            name=R.prop(node_name_key, raw_node),
                            isGeneralized=is_generalized,
                            properties=list(R.keys(properties)),
                            propertyValues=list(R.values(properties))
                        )
                    ]
                )
            }
        )

    raw_nodes = create_raw_nodes(resource)
    # Reduce the nodes
    nodes_by_stage = R.reduce(
        lambda accum, i_and_node: accumulate_nodes(accum, i_and_node[1], i_and_node[0]),
        {},
        enumerate(raw_nodes)
    )
    nodes = R.flatten(R.values(nodes_by_stage))
    return dict(
        nodes=nodes,
        nodes_by_stage=nodes_by_stage,
        links=create_links(stages, value_key, nodes_by_stage)
    )


def accumulate_sankey_graph(accumulated_graph, resource):
    """
        Given an accumulated graph and
        and a current Resource object, process the resource object and add the results to the accumulated graph
    :param accumulated_graph:
    :param resource: A Resource
    :return:
    """

    links = R.item_path(['graph', 'links'], resource.data)
    nodes = R.item_path(['graph', 'nodes'], resource.data)

    # Combine the nodes and link with previous accumulated_graph nodes and links
    return dict(
        nodes=R.concat(R.prop_or([], 'nodes', accumulated_graph), nodes),
        # Naively create a link between every node of consecutive stages
        links=R.concat(R.prop_or([], 'links', accumulated_graph), links)
    )


def index_sankey_graph(graph):
    """
        Once all nodes are generated for a sankey graph the nodes need indices.
        This updates each node with and index property. Links also need the node indices,
        so each link gets source and target based on its source_node and target_node
    :param graph:
    :return: Updates graph.nodes, adding an index to each
    """

    nodes = R.prop('nodes', graph)
    for (i, node) in enumerate(nodes):
        node['index'] = i
    for link in R.prop('links', graph):
        link['source'] = nodes.index(R.prop('source_node', link))
        link['target'] = nodes.index(R.prop('target_node', link))


def create_sankey_graph_from_resources(resources):
    """
        Given Sankey data process it into Sankey graph data
    :param resources: Resource instances
    :return:
    """
    unindexed_graph = R.reduce(
        accumulate_sankey_graph,
        dict(nodes=[], links=[]),
        resources
    )
    return index_sankey_graph(unindexed_graph)


def add_sankey_graph_to_resource_dict(resource_dict):
    """
        Generate a sankey graph and "set" resource_dict.data.graph to it
    :param resource_dict: A resource instance with enough data to generate a graph
    :return: The copied resource_dict with data.graph set
    """
    graph = generate_sankey_data(resource_dict)
    # Updates the graph
    index_sankey_graph(graph)
    return R.fake_lens_path_set(['data', 'graph'], graph, resource_dict)
