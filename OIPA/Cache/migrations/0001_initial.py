# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import Cache.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='cached_call',
            fields=[
                ('call', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('last_fetched', models.DateTimeField(default=None, null=True)),
                ('result', Cache.models.MediumTextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='requested_call',
            fields=[
                ('call', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('cached', models.BooleanField(default=False)),
                ('response_time', models.DecimalField(null=True, max_digits=5, decimal_places=2)),
                ('last_requested', models.DateTimeField(auto_now=True)),
                ('count', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
