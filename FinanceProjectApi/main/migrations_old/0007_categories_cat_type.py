# Generated by Django 3.2.9 on 2021-11-28 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_auto_20211125_1721'),
    ]

    operations = [
        migrations.AddField(
            model_name='categories',
            name='cat_type',
            field=models.CharField(choices=[('exp', 'Расходы'), ('inc', 'Доходы')], default='exp', max_length=3),
        ),
    ]
