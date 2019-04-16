from django.db import transaction
from graphene import InputObjectType, Mutation, Field
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from rescape_graphene import REQUIRE, graphql_update_or_create, graphql_query, guess_update_or_create, \
    CREATE, UPDATE, input_type_parameters_for_update_or_create, input_type_fields, merge_with_django_properties, \
    DENY, FeatureCollectionDataType, resolver_for_dict_field
from rescape_graphene.schema_models.geojson.types.feature_collection import feature_collection_data_type_fields
from rescape_python_helpers import ramda as R
from rescape_graphene import increment_prop_until_unique, enforce_unique_props

from rescape_region.models.settings import Settings
from .settings_data_schema import SettingsDataType, settings_data_fields

raw_settings_fields = dict(
    id=dict(create=DENY, update=REQUIRE),
    key=dict(create=REQUIRE),
    # This refers to the SettingsDataType, which is a representation of all the json fields of Settings.data
    data=dict(graphene_type=SettingsDataType, fields=settings_data_fields, default=lambda: dict()),
)


class SettingsType(DjangoObjectType):

    class Meta:
        model = Settings


# Modify data field to use the resolver.
# I guess there's no way to specify a resolver upon field creation, since graphene just reads the underlying
# Django model to generate the fields
SettingsType._meta.fields['data'] = Field(SettingsDataType, resolver=resolver_for_dict_field)

settings_fields = merge_with_django_properties(SettingsType, raw_settings_fields)

settings_mutation_config = dict(
    class_name='Settings',
    crud={
        CREATE: 'createSettings',
        UPDATE: 'updateSettings'
    },
    resolve=guess_update_or_create
)


class UpsertSettings(Mutation):
    """
        Abstract base class for mutation
    """
    settings = Field(SettingsType)

    @transaction.atomic
    @login_required
    def mutate(self, info, settings_data=None):
        # We must merge in existing settings.data if we are updating data
        if R.has('id', settings_data) and R.has('data', settings_data):
            # New data gets priority, but this is a deep merge.
            settings_data['data'] = R.merge_deep(
                Settings.objects.get(id=settings_data['id']).data,
                settings_data['data']
            )

        # Make sure that all props are unique that must be, either by modifying values or erring.
        modified_settings_data = enforce_unique_props(settings_fields, settings_data)
        update_or_create_values = input_type_parameters_for_update_or_create(settings_fields, modified_settings_data)

        settings, created = Settings.objects.update_or_create(**update_or_create_values)
        return UpsertSettings(settings=settings)


class CreateSettings(UpsertSettings):
    """
        Create Settings mutation class
    """

    class Arguments:
        settings_data = type('CreateSettingsInputType', (InputObjectType,),
                           input_type_fields(settings_fields, CREATE, SettingsType))(required=True)


class UpdateSettings(UpsertSettings):
    """
        Update Settings mutation class
    """

    class Arguments:
        settings_data = type('UpdateSettingsInputType', (InputObjectType,),
                           input_type_fields(settings_fields, UPDATE, SettingsType))(required=True)


graphql_update_or_create_settings = graphql_update_or_create(settings_mutation_config, settings_fields)
graphql_query_settings = graphql_query(SettingsType, settings_fields, 'settings')
