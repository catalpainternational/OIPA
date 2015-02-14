# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='codelist_sync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'codelist synchronisers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='dataset_sync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('interval', models.CharField(max_length=55, verbose_name='Interval', choices=[('YEARLY', 'Parse yearly'), ('MONTHLY', 'Parse monthly'), ('WEEKLY', 'Parse weekly'), ('DAILY', 'Parse daily')])),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('type', models.IntegerField(default=1, choices=[(1, 'Activity Files'), (2, 'Organisation Files')])),
            ],
            options={
                'verbose_name_plural': 'dataset synchronisers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='iati_xml_source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ref', models.CharField(help_text="Reference for the XML file. Preferred usage: 'collection' or single country or region name", max_length=70, verbose_name='Reference')),
                ('title', models.CharField(max_length=255, null=True)),
                ('type', models.IntegerField(default=1, choices=[(1, 'Activity Files'), (2, 'Organisation Files')])),
                ('source_url', models.CharField(help_text='Hyperlink to an IATI activity or organisation XML file.', unique=True, max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now_add=True)),
                ('update_interval', models.CharField(default=b'month', max_length=20, null=True, blank=True, choices=[(b'day', 'Day'), (b'week', 'Week'), (b'month', 'Month'), (b'year', 'Year')])),
                ('last_found_in_registry', models.DateTimeField(default=None, null=True)),
                ('xml_activity_count', models.IntegerField(default=None, null=True)),
                ('oipa_activity_count', models.IntegerField(default=None, null=True)),
            ],
            options={
                'ordering': ['ref'],
                'verbose_name_plural': 'IATI XML sources',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('org_id', models.CharField(max_length=100, null=True, blank=True)),
                ('org_abbreviate', models.CharField(max_length=55, null=True, blank=True)),
                ('org_name', models.CharField(max_length=255)),
                ('default_interval', models.CharField(default='MONTHLY', max_length=55, verbose_name='Interval', choices=[('YEARLY', 'Parse yearly'), ('MONTHLY', 'Parse monthly'), ('WEEKLY', 'Parse weekly'), ('DAILY', 'Parse daily')])),
            ],
            options={
                'ordering': ['org_name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='iati_xml_source',
            name='publisher',
            field=models.ForeignKey(to='IATI_synchroniser.Publisher'),
            preserve_default=True,
        ),
    ]
