# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-08 06:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('icefish', '0010_auto_20171108_1738'),
    ]

    operations = [
        migrations.AddField(
            model_name='ctd',
            name='weather',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='icefish.Weather'),
        ),
        migrations.AddField(
            model_name='weather',
            name='valid_from',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='weather',
            name='valid_to',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
