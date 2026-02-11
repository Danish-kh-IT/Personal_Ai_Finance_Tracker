from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'expenses', api_views.ExpenseViewSet, basename='expense')
router.register(r'budgets', api_views.BudgetViewSet, basename='budget')
router.register(r'categories', api_views.CategoryViewSet, basename='category')

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('list/', views.expense_list, name='expense_list'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<int:budget_id>/delete/', views.budget_delete, name='budget_delete'),
    path('expense/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('get-savings-tip/', views.get_savings_tip, name='get_savings_tip'),
    path('export/<str:format>/', views.export_expenses, name='export_expenses'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/advice/', api_views.AISavingsAdviceView.as_view(), name='api_advice'),
]