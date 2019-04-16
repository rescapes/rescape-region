# Generated by Django 2.0.7 on 2019-04-16 10:04

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import rescape_region.model_helpers


class Migration(migrations.Migration):

    dependencies = [
        ('rescape_region', '0005_auto_20190219_1443'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=20, unique=True)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default=rescape_region.model_helpers.user_state_data_default)),
            ],
        ),
    ]
