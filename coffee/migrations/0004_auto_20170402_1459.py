# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-02 11:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coffee', '0003_auto_20170402_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coffee',
            name='roaster_comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]
