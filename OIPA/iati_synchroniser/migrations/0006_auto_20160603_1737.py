# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 17:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iati_synchroniser', '0005_auto_20160603_1631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iatixmlsourcenote',
            name='iati_identifier',
            field=models.CharField(max_length=100),
        ),
    ]
