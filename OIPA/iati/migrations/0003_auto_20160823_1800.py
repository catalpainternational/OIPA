# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-23 09:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iati', '0002_migration'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='activityparticipatingorganisation',
            unique_together=set([('activity', 'organisation', 'role')]),
        ),
        migrations.AlterUniqueTogether(
            name='activitysector',
            unique_together=set([('activity', 'sector')]),
        ),
    ]