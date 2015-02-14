# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='activity',
            fields=[
                ('id', models.CharField(max_length=150, serialize=False, primary_key=True)),
                ('hierarchy', models.SmallIntegerField(default=1, null=True, blank=True, choices=[(1, 'Parent'), (2, 'Child')])),
                ('last_updated_datetime', models.CharField(default=None, max_length=100, null=True)),
                ('linked_data_uri', models.CharField(max_length=100, null=True, blank=True)),
                ('start_planned', models.DateField(default=None, null=True, blank=True)),
                ('end_planned', models.DateField(default=None, null=True, blank=True)),
                ('start_actual', models.DateField(default=None, null=True, blank=True)),
                ('end_actual', models.DateField(default=None, null=True, blank=True)),
                ('xml_source_ref', models.CharField(max_length=200, null=True, blank=True)),
                ('total_budget', models.DecimalField(decimal_places=2, default=None, max_digits=15, blank=True, null=True, db_index=True)),
                ('iati_identifier', models.CharField(max_length=150)),
            ],
            options={
                'verbose_name_plural': 'activities',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_date_type',
            fields=[
                ('code', models.CharField(max_length=20, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_participating_organisation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(default=None, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_policy_marker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('alt_policy_marker', models.CharField(default=None, max_length=200, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_recipient_country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('percentage', models.DecimalField(default=None, null=True, max_digits=5, decimal_places=2, blank=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('country', models.ForeignKey(to='geodata.country')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_recipient_region',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('percentage', models.DecimalField(default=None, null=True, max_digits=5, decimal_places=2)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('region', models.ForeignKey(to='geodata.region')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_sector',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('alt_sector_name', models.CharField(default=None, max_length=200, null=True)),
                ('percentage', models.DecimalField(default=None, null=True, max_digits=5, decimal_places=2, blank=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_status',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('language', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='activity_website',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=150)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='aid_type',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='aid_type_category',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='budget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period_start', models.CharField(default=None, max_length=50, null=True)),
                ('period_end', models.CharField(default=None, max_length=50, null=True)),
                ('value', models.DecimalField(max_digits=12, decimal_places=2)),
                ('value_date', models.DateField(default=None, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='budget_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('language', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='collaboration_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('language', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='condition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(default=None, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='condition_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('language', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='contact_info',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_name', models.CharField(default=None, max_length=100, null=True, blank=True)),
                ('organisation', models.CharField(default=None, max_length=100, null=True, blank=True)),
                ('telephone', models.CharField(default=None, max_length=100, null=True, blank=True)),
                ('email', models.TextField(default=None, null=True, blank=True)),
                ('mailing_address', models.TextField(default=None, null=True, blank=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='currency',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('language', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='description',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(default=None, null=True, db_index=True, blank=True)),
                ('rsr_description_type_id', models.IntegerField(default=None, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='description_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='disbursement_channel',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='document_category',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=1)),
                ('category_name', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='document_link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=200)),
                ('title', models.CharField(default=None, max_length=255, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('document_category', models.ForeignKey(default=None, to='IATI.document_category', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='file_format',
            fields=[
                ('code', models.CharField(max_length=30, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='finance_type',
            fields=[
                ('code', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=220)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='finance_type_category',
            fields=[
                ('code', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='flow_type',
            fields=[
                ('code', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='gazetteer_agency',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='geographical_precision',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='indicator_measure',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='language',
            fields=[
                ('code', models.CharField(max_length=2, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=80)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(default=None, max_length=1000, null=True)),
                ('type_description', models.CharField(default=None, max_length=200, null=True)),
                ('description', models.TextField(default=None, null=True)),
                ('adm_country_adm1', models.CharField(default=None, max_length=100, null=True)),
                ('adm_country_adm2', models.CharField(default=None, max_length=100, null=True)),
                ('adm_country_name', models.CharField(default=None, max_length=200, null=True)),
                ('percentage', models.DecimalField(default=None, null=True, max_digits=5, decimal_places=2, blank=True)),
                ('latitude', models.CharField(default=None, max_length=70, null=True)),
                ('longitude', models.CharField(default=None, max_length=70, null=True)),
                ('gazetteer_entry', models.CharField(default=None, max_length=70, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('adm_country_iso', models.ForeignKey(default=None, to='geodata.country', null=True)),
                ('description_type', models.ForeignKey(default=None, to='IATI.description_type', null=True)),
                ('gazetteer_ref', models.ForeignKey(default=None, to='IATI.gazetteer_agency', null=True)),
                ('precision', models.ForeignKey(default=None, to='IATI.geographical_precision', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='location_type',
            fields=[
                ('code', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='organisation',
            fields=[
                ('code', models.CharField(max_length=30, serialize=False, primary_key=True)),
                ('abbreviation', models.CharField(default=None, max_length=30, null=True)),
                ('reported_by_organisation', models.CharField(default=None, max_length=100, null=True)),
                ('name', models.CharField(default=None, max_length=250, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='organisation_identifier',
            fields=[
                ('code', models.CharField(max_length=20, serialize=False, primary_key=True)),
                ('abbreviation', models.CharField(default=None, max_length=30, null=True)),
                ('name', models.CharField(default=None, max_length=250, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='organisation_role',
            fields=[
                ('code', models.CharField(max_length=20, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='organisation_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='other_identifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('owner_ref', models.CharField(default=None, max_length=100, null=True)),
                ('owner_name', models.CharField(default=None, max_length=100, null=True)),
                ('identifier', models.CharField(max_length=100)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='planned_disbursement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period_start', models.CharField(default=None, max_length=100, null=True)),
                ('period_end', models.CharField(default=None, max_length=100, null=True)),
                ('value_date', models.DateField(null=True)),
                ('value', models.DecimalField(max_digits=12, decimal_places=2)),
                ('updated', models.DateField(default=None, null=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('currency', models.ForeignKey(default=None, to='IATI.currency', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='policy_marker',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='policy_significance',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='publisher_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='related_activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ref', models.CharField(default=None, max_length=200, null=True)),
                ('text', models.TextField(default=None, null=True)),
                ('current_activity', models.ForeignKey(related_name='current_activity', to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='related_activity_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=None, max_length=200, null=True, blank=True)),
                ('description', models.TextField(default=None, null=True, blank=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='result_type',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='sector',
            fields=[
                ('code', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='sector_category',
            fields=[
                ('code', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='tied_status',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('language', models.ForeignKey(default=None, to='IATI.language', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(default=None, null=True, blank=True)),
                ('provider_organisation_name', models.CharField(default=None, max_length=200, null=True, blank=True)),
                ('provider_activity', models.CharField(max_length=100, null=True, blank=True)),
                ('receiver_organisation_name', models.CharField(default=None, max_length=200, null=True, blank=True)),
                ('transaction_date', models.DateField(default=None, null=True, blank=True)),
                ('value_date', models.DateField(default=None, null=True, blank=True)),
                ('value', models.DecimalField(max_digits=15, decimal_places=2)),
                ('ref', models.CharField(default=None, max_length=100, null=True, blank=True)),
                ('activity', models.ForeignKey(to='IATI.activity')),
                ('aid_type', models.ForeignKey(default=None, blank=True, to='IATI.aid_type', null=True)),
                ('currency', models.ForeignKey(default=None, blank=True, to='IATI.currency', null=True)),
                ('description_type', models.ForeignKey(default=None, blank=True, to='IATI.description_type', null=True)),
                ('disbursement_channel', models.ForeignKey(default=None, blank=True, to='IATI.disbursement_channel', null=True)),
                ('finance_type', models.ForeignKey(default=None, blank=True, to='IATI.finance_type', null=True)),
                ('flow_type', models.ForeignKey(default=None, blank=True, to='IATI.flow_type', null=True)),
                ('provider_organisation', models.ForeignKey(related_name='transaction_providing_organisation', default=None, blank=True, to='IATI.organisation', null=True)),
                ('receiver_organisation', models.ForeignKey(related_name='transaction_receiving_organisation', default=None, blank=True, to='IATI.organisation', null=True)),
                ('tied_status', models.ForeignKey(default=None, blank=True, to='IATI.tied_status', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='transaction_type',
            fields=[
                ('code', models.CharField(max_length=2, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='value_type',
            fields=[
                ('code', models.CharField(max_length=2, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='verification_status',
            fields=[
                ('code', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='vocabulary',
            fields=[
                ('code', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=140)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='transaction',
            name='transaction_type',
            field=models.ForeignKey(default=None, blank=True, to='IATI.transaction_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='result',
            name='result_type',
            field=models.ForeignKey(default=None, blank=True, to='IATI.result_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='related_activity',
            name='type',
            field=models.ForeignKey(default=None, to='IATI.related_activity_type', max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organisation',
            name='type',
            field=models.ForeignKey(default=None, to='IATI.organisation_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='type',
            field=models.ForeignKey(default=None, to='IATI.location_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='finance_type',
            name='category',
            field=models.ForeignKey(to='IATI.finance_type_category'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document_link',
            name='file_format',
            field=models.ForeignKey(default=None, to='IATI.file_format', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='description',
            name='language',
            field=models.ForeignKey(default=None, to='IATI.language', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='description',
            name='type',
            field=models.ForeignKey(related_name='description_type', default=None, to='IATI.description_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='condition',
            name='type',
            field=models.ForeignKey(default=None, to='IATI.condition_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='budget',
            name='currency',
            field=models.ForeignKey(default=None, to='IATI.currency', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='budget',
            name='type',
            field=models.ForeignKey(default=None, to='IATI.budget_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aid_type',
            name='category',
            field=models.ForeignKey(to='IATI.aid_type_category'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_sector',
            name='sector',
            field=models.ForeignKey(default=None, to='IATI.sector', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_sector',
            name='vocabulary',
            field=models.ForeignKey(default=None, to='IATI.vocabulary', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_policy_marker',
            name='policy_marker',
            field=models.ForeignKey(default=None, to='IATI.policy_marker', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_policy_marker',
            name='policy_significance',
            field=models.ForeignKey(default=None, to='IATI.policy_significance', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_policy_marker',
            name='vocabulary',
            field=models.ForeignKey(default=None, to='IATI.vocabulary', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_participating_organisation',
            name='organisation',
            field=models.ForeignKey(default=None, to='IATI.organisation', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity_participating_organisation',
            name='role',
            field=models.ForeignKey(default=None, to='IATI.organisation_role', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='activity_status',
            field=models.ForeignKey(default=None, blank=True, to='IATI.activity_status', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='collaboration_type',
            field=models.ForeignKey(default=None, blank=True, to='IATI.collaboration_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='default_aid_type',
            field=models.ForeignKey(default=None, blank=True, to='IATI.aid_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='default_currency',
            field=models.ForeignKey(related_name='default_currency', default=None, to='IATI.currency', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='default_finance_type',
            field=models.ForeignKey(default=None, blank=True, to='IATI.finance_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='default_flow_type',
            field=models.ForeignKey(default=None, blank=True, to='IATI.flow_type', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='default_tied_status',
            field=models.ForeignKey(default=None, blank=True, to='IATI.tied_status', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='participating_organisation',
            field=models.ManyToManyField(to='IATI.organisation', null=True, through='IATI.activity_participating_organisation', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='policy_marker',
            field=models.ManyToManyField(to='IATI.policy_marker', null=True, through='IATI.activity_policy_marker', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='recipient_country',
            field=models.ManyToManyField(to='geodata.country', through='IATI.activity_recipient_country'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='recipient_region',
            field=models.ManyToManyField(to='geodata.region', through='IATI.activity_recipient_region'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='reporting_organisation',
            field=models.ForeignKey(related_name='activity_reporting_organisation', default=None, blank=True, to='IATI.organisation', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='sector',
            field=models.ManyToManyField(to='IATI.sector', null=True, through='IATI.activity_sector', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activity',
            name='total_budget_currency',
            field=models.ForeignKey(related_name='total_budget_currency', default=None, blank=True, to='IATI.currency', null=True),
            preserve_default=True,
        ),
    ]
