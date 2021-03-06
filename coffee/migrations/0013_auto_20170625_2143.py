# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-06-25 18:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coffee', '0012_auto_20170613_1452'),
    ]

    operations = [
        migrations.CreateModel(
            name='BagPicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(blank=True, max_length=512, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='coffeebag',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='bags/full/'),
        ),
        migrations.AddField(
            model_name='coffeebag',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='bags/thumbs/'),
        ),
        migrations.AddField(
            model_name='bagpicture',
            name='bag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coffee.CoffeeBag'),
        ),
    ]
