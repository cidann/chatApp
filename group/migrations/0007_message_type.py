# Generated by Django 4.0.4 on 2022-06-19 01:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0006_group_backgroundenabled_group_passwordenabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='type',
            field=models.TextField(default='message'),
            preserve_default=False,
        ),
    ]
