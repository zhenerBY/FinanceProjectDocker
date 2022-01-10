from django.contrib import admin

from .models import AdvUser, Category, Operation, ApiUser


class AdvUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'is_superuser', 'is_active')
    list_display_links = ('username', 'first_name', 'last_name',)
    search_fields = ('username', 'first_name', 'last_name', 'email',)
    ordering = ('username',)


class ApiUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id', 'first_name', 'last_name', 'username', 'is_active', 'created_at', 'updated_at')
    list_display_links = ('chat_id',)
    search_fields = ('chat_id',)
    ordering = ('chat_id',)


class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'cat_type', 'created_at')
    list_display_links = ('name',)
    search_fields = ('name', 'user',)
    ordering = ('user', 'name',)


class OperationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'amount', 'user', 'category', 'created_at', 'is_active')
    list_display_links = ('title', 'user',)
    search_fields = ('title', 'description',)
    ordering = ('-created_at',)


admin.site.register(AdvUser, AdvUserAdmin)
admin.site.register(ApiUser, ApiUserAdmin)
admin.site.register(Category, CategoriesAdmin)
admin.site.register(Operation, OperationsAdmin)
