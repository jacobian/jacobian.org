# Generated by Django 2.1.3 on 2018-11-27 15:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0016_auto_20181121_1412'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photoset',
            name='photos',
        ),
        migrations.RemoveField(
            model_name='photoset',
            name='primary',
        ),
        migrations.DeleteModel(
            name='Photo',
        ),
        migrations.DeleteModel(
            name='Photoset',
        ),
    ]