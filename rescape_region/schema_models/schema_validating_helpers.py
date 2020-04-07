import re

from rescape_python_helpers.functional.ramda import pick_deep
from rescape_python_helpers import ramda as R


def quiz_model_query(client, model_query_function, result_name, variables):
    """
        Tests a query for a model with variables that produce exactly one result
    :param client: Apollo client
    :param model_query_function: Query function expecting the client and variables
    :param result_name: The name of the result object in the data object
    :param variables: key value variables for the query
    :return: void
    """
    all_result = model_query_function(client)
    assert not R.has('errors', all_result), R.dump_json(R.prop('errors', all_result))
    result = model_query_function(
        client,
        variables=variables
    )
    # Check against errors
    assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
    # Simple assertion that the query looks good
    assert 1 == R.length(R.item_path(['data', result_name], result))


def quiz_model_mutation_create(client, graphql_update_or_create_function, result_path, values,
                               second_create_results=None, second_create_does_update=False):
    """
        Tests a create mutation for a model
    :param client: The Apollo Client
    :param graphql_update_or_create_function: The update or create mutation function for the model. Expects client and input values
    :param result_path: The path to the result of the create in the data object (e.g. createRegion.region)
    :param values: The input values to use for the create
    :param second_create_results: Tests a second create if specified. Use to make sure that create with the same values
    creates a new instance or updates, depending on what you expect it to do.
    :param second_create_does_update: Default False. If True expects a second create with the same value to update rather than create a new instance
    :return:
    """
    result = graphql_update_or_create_function(client, values=values)
    result_path_partial = R.item_str_path(f'data.{result_path}')
    assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
    # Get the created value
    created = result_path_partial(result)
    # get all the keys in values that are in created. This should match values if created has everything we expect
    assert values == pick_deep(created, values)
    # Try creating with the same values again, unique constraints will apply to force a create or an update will occur
    if second_create_results:
        new_result = graphql_update_or_create_function(client, values)
        assert not R.has('errors', new_result), R.dump_json(R.prop('errors', new_result))
        created_too = result_path_partial(new_result)
        if second_create_does_update:
            assert created['id'] == created_too['id']
        if not second_create_does_update:
            assert created['id'] != created_too['id']
        assert second_create_results == pick_deep(second_create_results, created_too)


def quiz_model_mutation_update(client, graphql_update_or_create_function, create_path, update_path, values,
                               update_values):
    """
        Tests an update mutation for a model by calling a create with the given values then an update
        with the given update_values (plus the create id)
    :param client: The Apollo Client
    :param graphql_update_or_create_function: The update or create mutation function for the model. Expects client and input values
    :param create_path: The path to the result of the create in the data object (e.g. createRegion.region)
    :param update_path: The path to the result of the update in the data object (e.g. updateRegion.region)
    :param values: The input values to use for the create
    :param update_values: The input values to use for the update. This can be as little as one key value
    :return:
    """
    result = graphql_update_or_create_function(client, values=values)
    assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
    created = R.item_str_path(f'data.{create_path}', result)
    # look at the users added and omit the non-determinant dateJoined
    assert values == pick_deep(created, values)
    # Update with the id and optionally key if there is one + update_values
    new_result = graphql_update_or_create_function(
        client,
        R.merge_all([
            dict(
                id=int(created['id'])
            ),
            dict(
                key=created['key']
            ) if R.prop_or(False, 'key', created) else {},
            update_values
        ])
    )
    assert not R.has('errors', new_result), R.dump_json(R.prop('errors', new_result))
    updated = R.item_str_path(f'data.{update_path}', new_result)
    # TODO grapqhl returns ids now, so this can probable be removed
    # Since graphql ID type outputs string ids, but our input type is an int, convert all non-nil ids
    # Since OpenStreetMap can have actual string ids we want to leave those alone
    #pattern = re.compile("^\d+$")
    #updated_with_int_ids = R.map_with_obj_deep(
    #    lambda k, v: int(v) if R.equals('id', k) and pattern.search(v or '') else v, updated)
    assert created['id'] == updated['id']
    assert update_values == pick_deep(
        update_values,
        updated
    )
