# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-24 01:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('icefish', '0012_auto_20171118_1352'),
    ]

    operations = [
        migrations.CreateModel(
            name='MOOVideo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_path', models.FilePathField()),
                ('transcoded_path', models.FilePathField()),
            ],
        ),
    ]