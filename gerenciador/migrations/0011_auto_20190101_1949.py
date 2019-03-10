# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-01 21:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gerenciador', '0010_auto_20190101_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='trabalho',
            name='titulo',
            field=models.CharField(default='', help_text='T\xedtulo do Trabalho', max_length=150),
        ),
        migrations.AlterField(
            model_name='trabalho',
            name='descricao',
            field=models.CharField(default='', help_text='Descri\xe7\xe3o do Trabalho', max_length=15000),
        ),
    ]
