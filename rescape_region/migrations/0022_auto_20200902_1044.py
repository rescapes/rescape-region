# Generated by Django 3.1 on 2020-09-02 10:44

from django.db import migrations, models
import rescape_region.model_helpers
import rescape_region.models.resource


class Migration(migrations.Migration):

    dependencies = [
        ('rescape_region', '0021_auto_20200803_0818'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupstate',
            name='data',
            field=models.JSONField(default=rescape_region.model_helpers.group_state_data_default),
        ),
        migrations.AlterField(
            model_name='location',
            name='data',
            field=models.JSONField(default=rescape_region.model_helpers.region_data_default),
        ),
        migrations.AlterField(
            model_name='location',
            name='geojson',
            field=models.JSONField(default=rescape_region.model_helpers.feature_collection_default),
        ),
        migrations.AlterField(
            model_name='project',
            name='data',
            field=models.JSONField(default=rescape_region.model_helpers.project_data_default),
        ),
        migrations.AlterField(
            model_name='project',
            name='geojson',
            field=models.JSONField(default=rescape_region.model_helpers.feature_collection_default),
        ),
        migrations.AlterField(
            model_name='region',
            name='data',
            field=models.JSONField(default=rescape_region.model_helpers.region_data_default),
        ),
        migrations.AlterField(
            model_name='region',
            name='geojson',
            field=models.fields.JSONField(default=rescape_region.model_helpers.feature_collection_default),
        ),
        migrations.AlterField(
            model_name='resource',
            name='data',
            field=models.JSONField(default=rescape_region.models.resource.default),
        ),
        migrations.AlterField(
            model_name='settings',
            name='data',
            field=models.JSONField(default=rescape_region.model_helpers.user_state_data_default),
        ),
        migrations.AlterField(
            model_name='userstate',
            name='data',
            field=models.JSONField(default=rescape_region.model_helpers.user_state_data_default),
        ),
    ]
