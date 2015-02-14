# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='income_level',
            fields=[
                ('id', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='indicator',
            fields=[
                ('id', models.CharField(max_length=50, serialize=False, primary_key=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('friendly_label', models.CharField(max_length=255, null=True, blank=True)),
                ('type_data', models.CharField(max_length=255, null=True, blank=True)),
                ('selection_type', models.CharField(max_length=255, null=True, blank=True)),
                ('deprivation_type', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='indicator_data',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.FloatField(null=True, blank=True)),
                ('year', models.IntegerField(max_length=5)),
                ('city', models.ForeignKey(to='geodata.city', null=True)),
                ('country', models.ForeignKey(to='geodata.country', null=True)),
                ('indicator', models.ForeignKey(to='indicators.indicator')),
                ('region', models.ForeignKey(to='geodata.region', null=True)),
            ],
            options={
                'verbose_name_plural': 'indicator data',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='indicator_source',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='indicator_topic',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('source_note', models.TextField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='lending_type',
            fields=[
                ('id', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='indicator',
            name='source',
            field=models.ForeignKey(blank=True, to='indicators.indicator_source', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='indicator',
            name='topic',
            field=models.ForeignKey(blank=True, to='indicators.indicator_topic', null=True),
            preserve_default=True,
        ),
    ]
