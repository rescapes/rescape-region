import logging

import pytest

from rescape_region.schema_models.schema import dump_errors, create_schema
from rescape_python_helpers import ramda as R
from rescape_region.helpers.sankey_helpers import create_sankey_graph_from_resources
from graphene.test import Client
from snapshottest import TestCase
from .resource_sample import sample_settings, delete_sample_resources, create_sample_resources
from .resource_schema import graphql_query_resources, graphql_update_or_create_resource

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['created', 'updated']
schema = create_schema()

@pytest.mark.django_db
class ResourceSchemaTestCase(TestCase):
    client = None
    region = None
    resource = None

    def setUp(self):
        self.client = Client(schema)
        delete_sample_resources()
        self.resources = create_sample_resources()
        self.regions = list(set(R.map(lambda resource: resource.region, self.resources)))
        # Create a graph for all resources
        # This modifies each
        self.graph = create_sankey_graph_from_resources(self.resources)

    def test_query(self):
        all_result = graphql_query_resources(self.client)
        assert not R.has('errors', all_result), R.dump_json(R.prop('errors', all_result))
        results = graphql_query_resources(self.client, dict(name='String'), variable_values=dict(name='Minerals'))
        # Check against errors
        assert not R.has('errors', results), R.dump_json(R.prop('errors', results))
        assert 1 == R.length(R.item_path(['data', 'resources'], results))

    def test_create(self):
        values = dict(
            name='Candy',
            region=dict(id=R.head(self.regions).id),
            data=R.merge(
                sample_settings,
                dict(
                    material='Candy',
                    raw_data=[
                        'Other Global Imports;Shipments, location generalized;51.309933, 3.055030;Source;22,469,843',
                        'Knauf (Danilith) BE;Waregemseweg 156-142 9790 Wortegem-Petegem, Belgium;50.864762, 3.479308;Conversion;657,245',
                        "MPRO Bruxelles;Avenue du Port 67 1000 Bruxelles, Belgium;50.867486, 4.352543;Distribution;18,632",
                        'Residential Buildings (all typologies);Everywhere in Brussels;NA;Demand;3,882,735',
                        'Duplex House Typology;Everywhere in Brussels;NA;Demand;13,544',
                        'Apartment Building Typology;Everywhere in Brussels;NA;Demand;34,643',
                        'New West Gypsum Recycling;9130 Beveren, Sint-Jansweg 9 Haven 1602, Kallo, Belgium;51.270229, 4.261048;Reconversion;87,565',
                        'Residential Buildings (all typologies);Everywhere in Brussels;NA;Sink;120,000',
                        'RecyPark South;1190 Forest, Belgium;50.810799, 4.314789;Sink;3,130',
                        'RecyPark Nord;Rue du Rupel, 1000 Bruxelles, Belgium;50.880181, 4.377136;Sink;1,162'
                    ]
                )
            )
        )
        result = graphql_update_or_create_resource(self.client, values)
        dump_errors(result)
        assert not R.has('errors', result), R.dump_json(R.prop('errors', result))
        # look at the users added and omit the non-determinant dateJoined
        result_path_partial = R.item_path(['data', 'createResource', 'resource'])
        self.assertMatchSnapshot(R.omit(omit_props, result_path_partial(result)))

    def test_update(self):
        values = dict(
            name='Candy',
            region=dict(id=R.head(self.regions).id),
            data=R.merge(
                sample_settings,
                dict(
                    material='Candy',
                    raw_data=[
                        'Other Global Imports;Shipments, location generalized;51.309933, 3.055030;Source;22,469,843',
                        'Knauf (Danilith) BE;Waregemseweg 156-142 9790 Wortegem-Petegem, Belgium;50.864762, 3.479308;Conversion;657,245',
                        "MPRO Bruxelles;Avenue du Port 67 1000 Bruxelles, Belgium;50.867486, 4.352543;Distribution;18,632",
                        'Residential Buildings (all typologies);Everywhere in Brussels;NA;Demand;3,882,735',
                        'Duplex House Typology;Everywhere in Brussels;NA;Demand;13,544',
                        'Apartment Building Typology;Everywhere in Brussels;NA;Demand;34,643',
                        'New West Gypsum Recycling;9130 Beveren, Sint-Jansweg 9 Haven 1602, Kallo, Belgium;51.270229, 4.261048;Reconversion;87,565',
                        'Residential Buildings (all typologies);Everywhere in Brussels;NA;Sink;120,000',
                        'RecyPark South;1190 Forest, Belgium;50.810799, 4.314789;Sink;3,130',
                        'RecyPark Nord;Rue du Rupel, 1000 Bruxelles, Belgium;50.880181, 4.377136;Sink;1,162'
                    ]
                )
            )
        )
        create_raw = graphql_update_or_create_resource(self.client, values)
        dump_errors(create_raw)
        assert not R.has('errors', create_raw), R.dump_json(R.prop('errors', create_raw))
        result_path_partial = R.item_path(['data', 'createResource', 'resource'])
        create_result = result_path_partial(create_raw)

        update_raw = graphql_update_or_create_resource(self.client, R.merge(values, dict(name='Popcorn', id=int(create_result['id']))))
        dump_errors(update_raw)
        assert not R.has('errors', update_raw), R.dump_json(R.prop('errors', update_raw))
        result_path_partial = R.item_path(['data', 'updateResource', 'resource'])
        update_result = result_path_partial(update_raw)
        # Assert same instance
        assert update_result['id'] == create_result['id']
        # Assert the name updated
        assert update_result['name'] == 'Popcorn'

    # def test_delete(self):
    #     self.assertMatchSnapshot(self.client.execute('''{
    #         resources {
    #             username,
    #             first_name,
    #             last_name,
    #             password
    #         }
    #     }'''))
