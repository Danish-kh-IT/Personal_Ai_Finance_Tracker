from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Expense, Category, Budget

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        allow_null=True
    )

    class Meta:
        model = Expense
        fields = ['id', 'user', 'item', 'amount', 'category', 'category_name', 'raw_text', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Uncategorized"

class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    # Calculated fields to display status
    spent_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    is_exceeded = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'user', 'category', 'category_name', 'amount', 'period',
            'created_at', 'updated_at', 
            'spent_amount', 'remaining_amount', 'percentage_used', 'is_exceeded'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Overall"

    def get_spent_amount(self, obj):
        return obj.get_spent_amount()

    def get_remaining_amount(self, obj):
        return obj.get_remaining_amount()

    def get_percentage_used(self, obj):
        return obj.get_percentage_used()

    def get_is_exceeded(self, obj):
        return obj.is_exceeded()
