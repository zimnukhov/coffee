# Generated by Django 4.2.14 on 2024-08-04 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coffee', '0021_auto_20181214_0026'),
    ]

    operations = [
        migrations.AddField(
            model_name='brew',
            name='water_tds',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='brew',
            name='extraction',
            field=models.SmallIntegerField(blank=True, choices=[(-1, 'Недоэкстрагирован'), (0, 'Сбалансирован'), (1, 'Переэкстрагирован')], null=True),
        ),
        migrations.AlterField(
            model_name='coffeebag',
            name='status',
            field=models.IntegerField(choices=[(0, 'Not finished'), (1, 'Finished'), (2, 'Thrown away'), (3, 'Given away'), (4, 'Lost')], default=0),
        ),
    ]