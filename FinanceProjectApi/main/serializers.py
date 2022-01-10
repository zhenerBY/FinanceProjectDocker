from rest_framework import serializers

from main.models import AdvUser, Category, Operation, ApiUser


class UsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdvUser
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            # 'operations',
        ]


class ApiUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiUser
        fields = [
            'id',
            'chat_id',
            'first_name',
            'last_name',
            'username',
            'is_active',
            'date_filter_start',
            'date_filter_end',
            'pin_message_id',
        ]


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'user',
            'cat_type',
        ]


class OperationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = [
            'id',
            'title',
            'description',
            'amount',
            'user',
            'category',
            'created_at',
            'is_active',
        ]


class ExtendedOperationsSerializer(serializers.ModelSerializer):
    user = ApiUsersSerializer()
    category = CategoriesSerializer()

    class Meta:
        model = Operation
        fields = [
            'id',
            'title',
            'description',
            'amount',
            'user',
            'category',
            'created_at',
            'is_active',
        ]
