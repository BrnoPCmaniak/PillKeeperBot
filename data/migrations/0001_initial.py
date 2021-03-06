# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-06 07:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Pill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.BigIntegerField()),
                ('user_id', models.BigIntegerField()),
                ('name', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='RepeatEveryDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pill', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='data.Pill')),
            ],
        ),
        migrations.CreateModel(
            name='RepeatEveryNthDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n', models.IntegerField()),
                ('pill', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='data.Pill')),
            ],
        ),
        migrations.CreateModel(
            name='Time',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField()),
                ('last_done', models.DateField(auto_now=True)),
                ('pill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Pill')),
            ],
        ),
        migrations.CreateModel(
            name='WeekDaysRepetion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField()),
                ('pill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Pill')),
            ],
        ),
    ]
