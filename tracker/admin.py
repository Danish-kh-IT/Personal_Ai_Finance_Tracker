from django.contrib import admin

# Register your models here.
from .models import Category, Expense, Budget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'amount', 'category', 'created_at')
    list_filter = ('category', 'created_at', 'user')
    search_fields = ('item', 'raw_text', 'user__username')
    date_hierarchy = 'created_at'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'period', 'created_at')
    list_filter = ('period', 'created_at', 'category')
    search_fields = ('user__username', 'category__name')
    date_hierarchy = 'created_at'
    
