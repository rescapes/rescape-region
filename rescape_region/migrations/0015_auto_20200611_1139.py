# Generated by Django 3.0.5 on 2020-06-11 11:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('rescape_region', '0014_auto_20200415_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userstate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
