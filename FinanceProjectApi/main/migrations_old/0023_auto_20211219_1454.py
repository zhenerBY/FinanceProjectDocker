# Generated by Django 3.2.9 on 2021-12-19 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_auto_20211219_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apiuser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='apiuser',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='Updated'),
        ),
    ]
