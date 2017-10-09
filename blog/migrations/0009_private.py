# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-09 02:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_entry_tweet_html'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogmark',
            name='private',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='entry',
            name='private',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quotation',
            name='private',
            field=models.BooleanField(default=False),
        ),
    ]