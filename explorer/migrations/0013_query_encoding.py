# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-01 12:27


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0012_query_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='encoding',
            field=models.CharField(blank=True, default=b'utf-8', max_length=100, null=True),
        ),
    ]
