# Generated by Django 3.2 on 2021-12-17 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rescape_region', '0034_alter_project_locations'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchlocation',
            name='category',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
