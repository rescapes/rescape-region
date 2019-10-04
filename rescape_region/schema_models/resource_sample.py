
from rescape_python_helpers import ramda as R

from rescape_region.models import Region
from rescape_region.schema_models.region_sample import create_sample_regions
from rescape_region.models.resource import Resource
from rescape_region.helpers.sankey_helpers import generate_sankey_data

sample_settings = dict(
    settings=dict(
        defaultLocation=[4.3517, 50.8503],
        # The columns of the raw_data
        columns=[
            'siteName',
            'location',
            'coordinates',
            'junctionStage',
            'annualTonnage'
        ],
        # The column name used to name each stage
        stageKey='junctionStage',
        # The column used for node and link values
        valueKey='annualTonnage',
        # The column of the node location, normally a string representing a 2 element array representing a lat/lon
        locationKey='coordinates',
        nodeNameKey='siteName',
        stages=[
            dict(key='source', name='Source', targets=['conversion']),
            dict(key='conversion', name='Conversion', targets=['distribution']),
            dict(key='distribution', name='Distribution', targets=['demand']),
            dict(key='demand', name='Demand', targets=['reconversion', 'sink']),
            dict(key='reconversion', name='Reconversion', targets=['demand']),
            dict(key='sink', name='Sink', targets=[])
        ]
    )
)

# Map the settings to merge it into each resource
# Settings are stored in resource.data.settings
sample_resources = R.map(
    lambda resource_data: R.merge_deep(
        resource_data,
        dict(
            data=sample_settings
        )
    ),
    [
        dict(
            key='minerals',
            name='Minerals',
            data=dict(
                material='Minerals',
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
        ),
        dict(
            key='metals',
            name='Metals',
            data=dict(
                material='Metals',
                rawData=[
                    'Other Global Imports;Shipments, location generalized;51.309933, 3.055030;Source;367,689',
                    'Arcelor Steel Belgium;Lammerdries 10, 2440 Geel, Belgium;51.145051, 4.939373;Conversion;27,872',
                    'Duplex House Typology;Everywhere in Brussels;NA;Demand;3,048',
                    'Apartment Building Typology;Everywhere in Brussels;NA;Demand;18,548',
                    'Residential Buildings (all typologies);Everywhere in Brussels;NA;Demand;75,404',
                    'Metallo Belgium;Nieuwe Dreef 33, 2340 Beerse, Belgium;51.318025, 4.817432;Reconversion;54,000',
                    'Private Sector Collection;Everywhere in Brussels;NA;Sink;96,316',
                    'RecyPark South;1190 Forest, Belgium;50.810799, 4.314789;Sink;101',
                    'RecyPark Nord;Rue du Rupel, 1000 Bruxelles, Belgium;50.880181, 4.377136;Sink;67'
                ]
            )
        ),

        dict(
            key='wood',
            name='Wood',
            data=dict(
                material='Wood',
                rawData=[
                    'Forêt de Soignes;Watermael-Boitsfort Belgium ;50.777072, 4.409960;Source;6,288',
                    'Germany Imports;Germany, nearest point;50.786952, 6.102697;Source;66,812',
                    'Netherlands Imports;Netherlans, nearest point;51.467197, 4.609125;Source;52,352',
                    'Other Global Imports;Shipments, location generalized;51.309933, 3.055030;Source;323,384',
                    'Barthel Pauls Sawmill;Pôle Ardenne Bois 1, 6671 Bovigny, Belgium;50.259872, 5.933474;Conversion;200,430',
                    "Lochten & Germeau;Bd de l’Humanité, 51, 1190 Vorst, Belgium;50.820974, 4.314469;Distribution; NA, only for directional/path",
                    'Duplex House Typology;Everywhere in Brussels;NA;Demand;1,955',
                    'Apartment Building Typology;Everywhere in Brussels;NA;Demand;11,250',
                    'Residential Buildings (all typologies);Everywhere in Brussels;NA;Demand;45,659',
                    'Rotor Deconstruction;Prévinairestraat / Rue Prévinaire 58 1070 Anderlecht;50.839714, 4.352730;Reconversion;15,462',
                    'PAC Uccle;Boulevard de la Deuxième Armée Britannique 625-667 1190 Forest, Belgium;50.801647, 4.305641;Sink;189',
                    'PAC Saint-Josse;Rue Verboeckhaven 39-17 1210 Saint-Josse-ten-Noode, Belgium;50.854094, 4.375173;Sink;126',
                    'PAC Woluwe-Saint-Pierre;Avenue du Parc de Woluwe 86-44 1160 Auderghem, Belgium;50.823228, 4.427453;Sink;63.08',
                    "PAC d’Auderghem/Watermael-Boitsfort;1860 chaussée de Wavre, 1160 Auderghem;50.809948, 4.445271;Sink;252.32",
                    "RecyPark South;1190 Forest, Belgium;50.810799, 4.314789;Sink;668",
                    "RecyPark Nord;Rue du Rupel, 1000 Bruxelles, Belgium;50.880181, 4.377136;Sink;445"
                ]
            )
        )
    ]
)


def delete_sample_resources():
    Resource.objects.all().delete()


@R.curry
def create_sample_resource(region, resource_dict):
    # Generate our sample resources, computing and storing their Sankey graph data
    graph = generate_sankey_data(resource_dict)
    data = R.merge(
        R.prop('data', resource_dict),
        dict(
            graph=graph
        )
    )
    # Save the resource with the complete dataa
    resource = Resource(**R.merge(resource_dict, dict(region=region, data=data)))
    resource.save()
    return resource


def create_sample_resources(regions):
    # Convert all sample resource dicts to persisted Resource instances
    resources = R.map(create_sample_resource(R.head(regions)), sample_resources)
    return resources
