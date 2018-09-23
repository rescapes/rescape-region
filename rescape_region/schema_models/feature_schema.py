from graphene_django import DjangoObjectType
from rescape_python_helpers import geometry_from_geojson
from graphene.types.generic import GenericScalar

from graphene import InputObjectType,   String, Mutation, Field

from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties
from rescape_python_helpers import ramda as R

from rescape_region.models.feature import Feature
from rescape_graphene import FeatureDataType, feature_data_type_fields


class FeatureType(DjangoObjectType):
    class Meta:
        model = Feature

feature_fields = merge_with_django_properties(FeatureType, dict(
    name=dict(),
    description=dict(),
    created_at=dict(),
    updated_at=dict(),
    geometry=dict(
        create=REQUIRE,
        graphene_type=FeatureDataType,
        fields=feature_data_type_fields
    ),
))

geometry_fields = dict(
    type=dict(type=String),
    coordinates=dict(type=GenericScalar)
)

feature_fields = merge_with_django_properties(FeatureType, dict(
    name=dict(),
    description=dict(),
    created_at=dict(),
    updated_at=dict(),
    geo=dict(create=REQUIRE, fields=geometry_fields)
))

feature_mutation_config = dict(
    class_name='Feature',
    crud={
        CREATE: 'createFeature',
        UPDATE: 'updateFeature'
    },
    resolve=guess_update_or_create
)

def mutate_feature(feature_data):
    """
        Features are often dependent objects, so they aren't mutated separately. Hence this method is exposed
        so other Mutation classes that contain features can update them in the database
    :param feature_data:
    :return:
    """
    # feature_data is in the graphql_geojson format, so extract it to the model format before saving
    feature_dict = R.merge(
        # Extract properties from the properties key
        R.prop_or({}, 'properties', feature_data),
        # Extract geometry to the original name (which is also geometry)
        {FeatureType._meta.geojson_field: geometry_from_geojson(R.prop('geometry', feature_data))}
    )
    update_or_create_values = input_type_parameters_for_update_or_create(feature_fields, feature_dict)
    if R.prop_or(False, 'id', feature_data):
        feature, created = Feature.objects.update_or_create(**update_or_create_values)
    else:
        feature = Feature(**update_or_create_values['defaults'])
        feature.save()
        created = True
    return feature, created


class UpsertFeature(Mutation):
    """
        Abstract base class for mutation
    """
    feature = Field(FeatureType)

    def mutate(self, info, feature_data=None):
        feature, created = mutate_feature(feature_data)
        return UpsertFeature(feature=feature)

class CreateFeature(UpsertFeature):
    """
        Create Feature mutation class
    """

    class Arguments:
        feature_data = type('CreateFeatureInputType', (InputObjectType,),
                            input_type_fields(feature_fields, CREATE, FeatureType))(required=True)


class UpdateFeature(UpsertFeature):
    """
        Update Feature mutation class
    """

    class Arguments:
        feature_data = type('UpdateFeatureInputType', (InputObjectType,),
                            input_type_fields(feature_fields, UPDATE, FeatureType))(required=True)


graphql_update_or_create_feature = graphql_update_or_create(feature_mutation_config, feature_fields)
graphql_query_features = graphql_query('features', feature_fields)
