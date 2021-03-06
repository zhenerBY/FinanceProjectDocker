# Generated by Django 3.2.9 on 2021-11-25 12:49

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20211125_1457'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='Нименование категории')),
                ('expense', models.BooleanField(blank=True, db_index=True, default=None, null=True, verbose_name='Расход?')),
                ('income', models.BooleanField(blank=True, db_index=True, default=None, null=True, verbose_name='Доход?')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создано')),
            ],
            options={
                'verbose_name': 'Категория расходов',
                'verbose_name_plural': 'Категории расходов',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Operations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='Название')),
                ('description', models.TextField(verbose_name='Описание')),
                ('amount', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0, message='Значение меньше нуля')], verbose_name='Величина')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создано')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.categories', verbose_name='Категория')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Операция',
                'verbose_name_plural': 'Операции',
                'ordering': ('-created_at',),
            },
        ),
        migrations.DeleteModel(
            name='CategoriesExpenses',
        ),
        migrations.DeleteModel(
            name='Expenses',
        ),
    ]
