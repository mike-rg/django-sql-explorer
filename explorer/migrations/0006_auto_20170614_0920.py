# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-14 09:20


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0005_auto_20160105_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='bucket',
            field=models.CharField(default='empty', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='query',
            name='snapshot',
            field=models.BooleanField(default=True, help_text=b'Include in snapshot task (if enabled)'),
        ),
    ]
