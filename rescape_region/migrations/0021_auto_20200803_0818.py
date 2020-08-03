# Generated by Django 3.0.8 on 2020-08-03 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rescape_region', '0020_auto_20200803_0817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='key',
            field=models.CharField(max_length=50),
        ),
        migrations.AddConstraint(
            model_name='resource',
            constraint=models.UniqueConstraint(fields=('deleted', 'key'), name='unique_resource_with_deleted'),
        ),
        migrations.AddConstraint(
            model_name='resource',
            constraint=models.UniqueConstraint(condition=models.Q(deleted=None), fields=('key',), name='unique_resource_without_deleted'),
        ),
    ]
