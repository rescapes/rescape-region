import logging

import pytest
from rescape_graphene import client_for_testing
from rescape_python_helpers import ramda as R
from reversion.models import Version
from snapshottest import TestCase

from rescape_region.helpers.sankey_helpers import create_sankey_graph_from_resources
from rescape_region.models import Region, Resource
from rescape_region.schema_models.scope.region.region_sample import create_sample_regions
from rescape_region.schema_models.schema import create_default_schema
from rescape_graphene.graphql_helpers.schema_validating_helpers import quiz_model_query, quiz_model_mutation_create, \
    quiz_model_mutation_update
from rescape_region.schema_models.user_sample import create_sample_users
from .resource_sample import sample_settings, delete_sample_resources, create_sample_resources
from .resource_schema import graphql_query_resources, graphql_update_or_create_resource

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
omit_props = ['created', 'updated']
schema = create_default_schema()


@pytest.mark.django_db
class ResourceSchemaTestCase(TestCase):
    client = None
    region = None
    resource = None

    def setUp(self):
        users = create_sample_users()
        self.client = client_for_testing(schema, users[0])
        delete_sample_resources()
        self.region = R.head(create_sample_regions(Region))
        self.resources = create_sample_resources([self.region])
        # Create a graph for all resources
        # This modifies each node to have a node_index
        self.graph = create_sankey_graph_from_resources(self.resources)

    def test_query(self):
        quiz_model_query(self.client, graphql_query_resources, 'resources', dict(
            region=dict(id=self.region.id),
            name='Minerals'
        ))

    def test_create(self):
        result, _ = quiz_model_mutation_create(
            self.client,
            graphql_update_or_create_resource,
            'createResource.resource',
            dict(
                key='candy',
                name='Candy',
                region=dict(id=self.region.id),
                data=R.merge(
                    sample_settings,
                    dict(
                        material='Candy',
                        rawData=[
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
        )
        versions = Version.objects.get_for_object(Resource.objects.get(
            id=R.item_str_path('data.createResource.resource.id', result)
        ))
        assert len(versions) == 1

    def test_update(self):
        result, update_result = quiz_model_mutation_update(
            self.client,
            graphql_update_or_create_resource,
            'createResource.resource',
            'updateResource.resource',
            dict(
                key='candy',
                name='Candy',
                region=dict(id=self.region.id),
                data=R.merge(
                    sample_settings,
                    dict(
                        material='Candy',
                        rawData=[
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
            ),
            dict(
                key='popcorn',
                name='Popcorn'
            )
        )
        versions = Version.objects.get_for_object(Resource.objects.get(
            id=R.item_str_path('data.updateResource.resource.id', update_result)
        ))
        assert len(versions) == 2
