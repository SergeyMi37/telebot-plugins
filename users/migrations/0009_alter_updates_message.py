# Generated by Django 3.2.9 on 2025-07-21 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20250719_0805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='updates',
            name='message',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
