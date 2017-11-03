# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-31 07:29
# Empty migration generated in order to load default CTD into database

from __future__ import unicode_literals

from django.db import migrations

from icefish_backend import local_settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('icefish', '0006_auto_20171103_1341'),
    ]

    operations = [
        migrations.RunSQL("INSERT INTO {}icefish_ctdinstrument (deployment_start) VALUES ({});".format(
            "icefish_backend." if 'postgres' in local_settings.DATABASES["default"]["ENGINE"] else "",
            "clock_timestamp()" if 'postgres' in local_settings.DATABASES["default"]["ENGINE"] else "DATETIME('now')")),

        migrations.AddField(
            model_name='ctd',
            name='instrument',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='icefish.CTDInstrument'),
            preserve_default=False,
        ),
    ]