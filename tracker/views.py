from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from .models import Expense, Category, Budget
from .ai_utils import parse_expense_with_ai, get_ai_budget_advice
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
import json
import csv
from django.http import HttpResponse
from openpyxl import Workbook
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO

@login_required
def add_expense(request):
    if request.method == "POST":
        user_text = request.POST.get('raw_text')
        
        # AI Extraction
        ai_data = parse_expense_with_ai(user_text)
        
        if ai_data:
            # Safely handle category mapping
            category_name = ai_data.get('category', 'Others')
            cat_obj, _ = Category.objects.get_or_create(name=category_name)
            
            # Save Expense
            expense = Expense.objects.create(
                user=request.user,
                item=ai_data.get('item', 'Miscellaneous'),
                amount=ai_data.get('amount', 0),
                category=cat_obj,
                raw_text=user_text
            )
            
            # Check for budget alerts after expense creation
            check_budget_alerts(request, request.user, expense)
            
            messages.success(request, f"Expense added: {expense.item} - {expense.amount}")
            return redirect('dashboard') 
        else:
            messages.error(request, 'AI could not process this. Please try again with more detail.')
            return render(request, 'tracker/add_expense.html', {
                'error': 'AI could not process this. Please try again with more detail.'
            })
            
    return render(request, 'tracker/add_expense.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    return render(request, 'tracker/signup.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

def check_budget_alerts(request, user, expense):
    """Check if expense triggers any budget alerts"""
    budgets = Budget.objects.filter(user=user)
    for budget in budgets:
        if budget.category == expense.category or budget.category is None:
            if budget.is_exceeded():
                messages.warning(
                    request,
                    f"⚠️ Budget Exceeded! {budget.category.name if budget.category else 'Overall'} budget ({budget.period}) exceeded by Rs. {abs(budget.get_remaining_amount()):.2f}"
                )
            elif budget.get_percentage_used() >= 90:
                messages.warning(
                    request,
                    f"⚠️ Budget Alert! {budget.category.name if budget.category else 'Overall'} budget ({budget.period}) is {budget.get_percentage_used():.1f}% used."
                )

@login_required
def budget_list(request):
    """View all budgets"""
    budgets = Budget.objects.filter(user=request.user).order_by('-created_at')
    budget_data = []
    for budget in budgets:
        budget_data.append({
            'budget': budget,
            'spent': budget.get_spent_amount(),
            'remaining': budget.get_remaining_amount(),
            'percentage': budget.get_percentage_used(),
            'exceeded': budget.is_exceeded()
        })
    return render(request, 'tracker/budget_list.html', {'budgets': budget_data})

@login_required
def budget_create(request):
    """Create or update budget"""
    budget_id = request.GET.get('id')
    budget = None
    if budget_id:
        budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        period = request.POST.get('period')
        
        category = None
        if category_id:
            category = get_object_or_404(Category, id=category_id)
        
        if budget:
            # Update existing budget
            budget.category = category
            budget.amount = amount
            budget.period = period
            budget.save()
            messages.success(request, 'Budget updated successfully!')
        else:
            # Create new budget
            budget, created = Budget.objects.update_or_create(
                user=request.user,
                category=category,
                period=period,
                defaults={'amount': amount}
            )
            if created:
                messages.success(request, 'Budget created successfully!')
            else:
                messages.success(request, 'Budget updated successfully!')
        
        return redirect('budget_list')
    
    categories = Category.objects.all()
    return render(request, 'tracker/budget_form.html', {
        'categories': categories,
        'budget': budget
    })

@login_required
def budget_delete(request, budget_id):
    """Delete a budget"""
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('budget_list')
    return render(request, 'tracker/budget_confirm_delete.html', {'budget': budget})

@login_required
def delete_expense(request, expense_id):
    """Delete an expense"""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    return redirect('dashboard')

@login_required
def expense_list(request):
    # History page ke liye logic
    expenses = Expense.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tracker/expense_list.html', {'expenses': expenses})

@login_required
def dashboard(request):
    # 1. Category-wise spending (Pie Chart)
    data = Expense.objects.filter(user=request.user).values('category__name').annotate(total=Sum('amount'))
    
    labels = [item['category__name'] if item['category__name'] else "Uncategorized" for item in data]
    values = [float(item['total']) for item in data]
    
    # 2. Trend Analysis - Last 30 days spending
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    daily_expenses = Expense.objects.filter(
        user=request.user,
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    trend_dates = [item['date'].strftime('%Y-%m-%d') if item['date'] else '' for item in daily_expenses]
    trend_amounts = [float(item['total']) for item in daily_expenses]
    
    # 3. Monthly Trend (Last 6 months)
    monthly_expenses = Expense.objects.filter(
        user=request.user
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')[:6]
    
    monthly_labels = [item['month'].strftime('%b %Y') if item['month'] else '' for item in monthly_expenses]
    monthly_values = [float(item['total']) for item in monthly_expenses]
    
    # 4. Recent Transactions
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # 5. Budget Alerts
    budgets = Budget.objects.filter(user=request.user)
    budget_alerts = []
    for budget in budgets:
        spent = budget.get_spent_amount()
        percentage = budget.get_percentage_used()
        if percentage >= 80:  # Alert if 80% or more used
            budget_alerts.append({
                'budget': budget,
                'spent': spent,
                'remaining': budget.get_remaining_amount(),
                'percentage': percentage,
                'exceeded': budget.is_exceeded()
            })
    
    # 6. Overall Statistics
    total_expenses = Expense.objects.filter(user=request.user).count()
    avg_expense = Expense.objects.filter(user=request.user).aggregate(avg=Sum('amount'))['avg'] or 0
    if total_expenses > 0:
        avg_expense = float(avg_expense) / total_expenses
    
    context = {
        'labels': json.dumps(labels),
        'values': json.dumps(values),
        'total_spent': sum(values) if values else 0,
        'recent_expenses': recent_expenses,
        'trend_dates': json.dumps(trend_dates),
        'trend_amounts': json.dumps(trend_amounts),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_values': json.dumps(monthly_values),
        'budget_alerts': budget_alerts,
        'total_expenses': total_expenses,
        'avg_expense': avg_expense,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def get_savings_tip(request):
    """
    API endpoint to fetch AI savings advice based on current month's spending.
    """
    # 1. Aggregate spending by category for the current month
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    expenses = Expense.objects.filter(
        user=request.user,
        created_at__gte=current_month
    ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    summary = []
    for item in expenses:
        cat_name = item['category__name'] if item['category__name'] else "Uncategorized"
        summary.append({'category': cat_name, 'total': float(item['total'])})
    
    if not summary:
        return JsonResponse({'advice': "No expenses recorded this month yet! Add some expenses to get advice."})
        
    # 2. Get AI Advice
    advice = get_ai_budget_advice(summary)
    
    return JsonResponse({'advice': advice})
@login_required
def export_expenses(request, format):
    """Export expenses in specified format"""
    expenses = Expense.objects.filter(user=request.user).order_by('-created_at')
    
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expenses_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Item', 'Category', 'Amount', 'Original Text'])
        
        for expense in expenses:
            writer.writerow([
                expense.created_at.strftime("%Y-%m-%d %H:%M"),
                expense.item,
                expense.category.name if expense.category else "Uncategorized",
                expense.amount,
                expense.raw_text
            ])
        return response

    elif format == 'excel':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="expenses_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Expenses"
        
        # Headers
        headers = ['Date', 'Item', 'Category', 'Amount', 'Original Text']
        ws.append(headers)
        
        # Data
        for expense in expenses:
            ws.append([
                expense.created_at.strftime("%Y-%m-%d %H:%M"),
                expense.item,
                expense.category.name if expense.category else "Uncategorized",
                float(expense.amount),
                expense.raw_text
            ])
            
        wb.save(response)
        return response

    elif format == 'pdf':
        template_path = 'tracker/expense_report_pdf.html'
        context = {
            'expenses': expenses,
            'user': request.user,
            'today': timezone.now(),
            'total_amount': expenses.aggregate(total=Sum('amount'))['total'] or 0
        }
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="expenses_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)
        
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse('We had some errors while generating PDF.')
        return response

    return redirect('expense_list')
