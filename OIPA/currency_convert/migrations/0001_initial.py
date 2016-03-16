# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-16 12:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('iati_codelists', '0003_auto_20160204_1305'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyAverage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField()),
                ('year', models.IntegerField()),
                ('value', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=5, null=True)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='iati_codelists.Currency')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='monthlyaverage',
            unique_together=set([('currency', 'month', 'year')]),
        ),
    ]
