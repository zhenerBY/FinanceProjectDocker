from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class AdvUser(AbstractUser):
    is_activated = models.BooleanField(default=True,
                                       db_index=True,
                                       verbose_name=_('Activated?'))

    class Meta(AbstractUser.Meta):
        pass


class ApiUser(models.Model):
    first_name = models.CharField(max_length=255,
                                  db_index=True,
                                  null=True,
                                  blank=True,
                                  verbose_name=_('First name'))
    last_name = models.CharField(max_length=255,
                                 db_index=True,
                                 null=True,
                                 blank=True,
                                 verbose_name=_('Last name'),
                                 default=None,
                                 )
    username = models.CharField(max_length=255,
                                db_index=True,
                                null=True,
                                blank=True,
                                verbose_name=_('User name'),
                                default=None,
                                )
    chat_id = models.PositiveBigIntegerField(unique=True)
    is_active = models.BooleanField(default=True,
                                    verbose_name=_('Is active?'))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_('Created'))
    updated_at = models.DateTimeField(auto_now=True, db_index=True, verbose_name=_('Updated'))
    date_filter_start = models.DateField(null=True, blank=True, default=None, verbose_name=_('Date filter start'))
    date_filter_end = models.DateField(null=True, blank=True, default=None, verbose_name=_('Date filter end'))
    pin_message_id = models.IntegerField(null=True, blank=True, default=None, verbose_name=_('Pinned message id'))

    def __str__(self):
        return f'ApiUser - {self.chat_id}'

    class Meta:
        ordering = ('chat_id',)
        verbose_name = _('API User')
        verbose_name_plural = _('API Users')


class Category(models.Model):
    class CatType(models.TextChoices):
        EXPENSE = 'EXP', _('Expense')
        INCOME = 'INC', _('Income')

    name = models.CharField(max_length=50,
                            db_index=True,
                            unique=True,
                            verbose_name=_('Category name'))
    cat_type = models.CharField(max_length=3, choices=CatType.choices, default=CatType.EXPENSE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_('Created'))
    user = models.ForeignKey(ApiUser, on_delete=models.CASCADE,
                             verbose_name=_('User'), related_name='user')

    def __str__(self):
        return f'Category - {self.user}|{self.name}: {self.cat_type}'

    class Meta:
        ordering = ('name',)
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')


class Operation(models.Model):
    title = models.CharField(max_length=50, verbose_name=_('Name'))
    description = models.TextField(verbose_name=_('Description'))
    amount = models.FloatField(default=0, verbose_name='Величина',
                               validators=[validators.MinValueValidator(0,
                                                                        message=_('Value less than zero'))])
    # Checking for only positive values
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_('Created'))
    user = models.ForeignKey(ApiUser, on_delete=models.CASCADE,
                             verbose_name=_('User'), related_name='operations')
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 verbose_name=_('Category'), related_name='operations')
    is_active = models.BooleanField(default=True,
                                    verbose_name=_('Is active?'))

    def __str__(self):
        return f"Operation - {self.title} {self.amount}"

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Operation')
        verbose_name_plural = _('Operations')

    pass
