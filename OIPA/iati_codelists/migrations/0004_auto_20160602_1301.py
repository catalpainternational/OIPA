# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-02 13:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iati_codelists', '0003_auto_20160204_1305'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetStatus',
            fields=[
                ('code', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20)),
                ('description', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='HumanitarianScopeType',
            fields=[
                ('code', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=160)),
                ('description', models.TextField(default=b'')),
            ],
        ),
        migrations.RemoveField(
            model_name='activitydatetype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='activitydatetype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='activityscope',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='activityscope',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='activitystatus',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='activitystatus',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='aidtype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='aidtype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='aidtypecategory',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='aidtypecategory',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='budgetidentifier',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='budgetidentifier',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='budgetidentifiersector',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='budgetidentifiersector',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='budgetidentifiersectorcategory',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='budgetidentifiersectorcategory',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='budgettype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='budgettype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='collaborationtype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='collaborationtype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='conditiontype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='conditiontype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='contacttype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='contacttype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='currency',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='currency',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='descriptiontype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='descriptiontype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='disbursementchannel',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='disbursementchannel',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='documentcategory',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='documentcategory',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='documentcategorycategory',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='documentcategorycategory',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='fileformat',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='fileformat',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='financetype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='financetype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='financetypecategory',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='financetypecategory',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='flowtype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='flowtype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='gazetteeragency',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='gazetteeragency',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='geographicalprecision',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='geographicalprecision',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='geographicexactness',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='geographicexactness',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='geographiclocationclass',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='geographiclocationclass',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='geographiclocationreach',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='geographiclocationreach',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='indicatormeasure',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='indicatormeasure',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='language',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='language',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='loanrepaymentperiod',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='loanrepaymentperiod',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='loanrepaymenttype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='loanrepaymenttype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='locationtype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='locationtype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='locationtypecategory',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='locationtypecategory',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='organisationidentifier',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='organisationidentifier',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='organisationregistrationagency',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='organisationregistrationagency',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='organisationrole',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='organisationrole',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='organisationtype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='organisationtype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='otherflags',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='otherflags',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='otheridentifiertype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='otheridentifiertype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='policysignificance',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='policysignificance',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='publishertype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='publishertype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='relatedactivitytype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='relatedactivitytype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='resulttype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='resulttype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='tiedstatus',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='tiedstatus',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='transactiontype',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='transactiontype',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='verificationstatus',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='verificationstatus',
            name='codelist_successor',
        ),
        migrations.RemoveField(
            model_name='version',
            name='codelist_iati_version',
        ),
        migrations.RemoveField(
            model_name='version',
            name='codelist_successor',
        ),
    ]
