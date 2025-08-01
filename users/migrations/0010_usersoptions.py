# Generated by Django 3.2.9 on 2025-07-25 11:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_updates_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsersOptions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('name', models.CharField(blank=True, help_text='Имя параметра', max_length=132, null=True, unique=True)),
                ('description', models.TextField(blank=True, default='', help_text='Описание параметра', verbose_name='Описание')),
                ('category', models.CharField(default='dflt', help_text='Категория параметра', max_length=256)),
                ('type', models.CharField(blank=True, default='str', help_text='Тип параметра', max_length=256, null=True)),
                ('value', models.TextField(default='', help_text='Значение параметра')),
                ('enabled', models.BooleanField(default=True, help_text='Включено')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
    ]
