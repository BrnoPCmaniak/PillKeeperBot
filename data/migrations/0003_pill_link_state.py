# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='pill',
            field=models.ForeignKey(default=None, blank=True, to='data.Pill', null=True),
        ),
        migrations.AlterField(
            model_name='state',
            name='state',
            field=models.IntegerField(default=0),
        ),
    ]
