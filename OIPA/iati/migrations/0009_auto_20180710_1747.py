# Generated by Django 2.0.6 on 2018-07-10 17:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iati', '0008_auto_20180710_1547'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activitytag',
            old_name='indicator_uri',
            new_name='vocabulary_uri',
        ),
    ]
