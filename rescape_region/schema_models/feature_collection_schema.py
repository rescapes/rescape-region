from graphene_django import DjangoObjectType
from rescape_graphene.schema_models.geojson.types.geometry_collection import geometry_collection_fields, \
    GeometryCollectionType
from rescape_python_helpers import geometry_from_geojson

from graphene import InputObjectType,  Mutation, Field

from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties

from rescape_python_helpers import ramda as R

from rescape_region.models.feature_collection import FeatureCollection


class FeatureCollectionType(DjangoObjectType):
    class Meta:
        model = FeatureCollection


feature_collection_fields = merge_with_django_properties(FeatureCollectionType, dict(
    name=dict(),
    description=dict(),
    created_at=dict(),
    updated_at=dict(),
    geo_collection=dict(
        create=REQUIRE,
        graphene_type=GeometryCollectionType,
        fields=geometry_collection_fields
    ),
))

feature_collection_mutation_config = dict(
    class_name='FeatureCollection',
    crud={
        CREATE: 'createFeatureCollection',
        UPDATE: 'updateFeatureCollection'
    },
    resolve=guess_update_or_create
)


def mutate_feature_collection(feature_collection_data):
    """
        FeatureCollections are often dependent objects, so they aren't mutated separately. Hence this method is exposed
        so other Mutation classes that contain feature_collections can update them in the database
    :param feature_collection_data:
    :return:
    """
    # feature_collection_data is in the graphql_geojson format, so extract it to the model format before saving
    feature_collection_dict = R.merge(
        # Extract properties from the properties key
        R.prop_or({}, 'properties', feature_collection_data),
        # Extract geometry to the original name (which is also geometry)
        {FeatureCollectionType._meta.geojson_field: geometry_from_geojson(R.prop('geometry', feature_collection_data))}
    )
    update_or_create_values = input_type_parameters_for_update_or_create(feature_collection_fields,
                                                                         feature_collection_dict)
    if R.prop_or(False, 'id', feature_collection_data):
        feature_collection, created = FeatureCollection.objects.update_or_create(**update_or_create_values)
    else:
        feature_collection = FeatureCollection(**update_or_create_values['defaults'])
        feature_collection.save()
        created = True
    return feature_collection, created


class UpsertFeatureCollection(Mutation):
    """
        Abstract base class for mutation
    """
    feature_collection = Field(FeatureCollectionType)

    def mutate(self, info, feature_collection_data=None):
        feature_collection, created = mutate_feature_collection(feature_collection_data)
        return UpsertFeatureCollection(feature_collection=feature_collection)


class CreateFeatureCollection(UpsertFeatureCollection):
    """
        Create FeatureCollection mutation class
    """

    class Arguments:
        feature_collection_data = type('CreateFeatureCollectionInputType', (InputObjectType,),
                                       input_type_fields(feature_collection_fields, CREATE, FeatureCollectionType))(
            required=True)


class UpdateFeatureCollection(UpsertFeatureCollection):
    """
        Update FeatureCollection mutation class
    """

    class Arguments:
        feature_collection_data = type('UpdateFeatureCollectionInputType', (InputObjectType,),
                                       input_type_fields(feature_collection_fields, UPDATE, FeatureCollectionType))(
            required=True)


graphql_update_or_create_feature_collection = graphql_update_or_create(feature_collection_mutation_config,
                                                                       feature_collection_fields)
graphql_query_feature_collections = graphql_query('feature_collections', feature_collection_fields)
