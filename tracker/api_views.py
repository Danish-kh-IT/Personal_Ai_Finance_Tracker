from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from django.utils import timezone
from .models import Expense, Category, Budget
from .serializers import ExpenseSerializer, CategorySerializer, BudgetSerializer
from .ai_utils import parse_expense_with_ai, get_ai_budget_advice

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.all()

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def add_with_ai(self, request):
        """
        Custom endpoint to add expense via AI natural language processing.
        Body: { "text": "Spent 500 on burger" }
        """
        text = request.data.get('text')
        if not text:
            return Response({"error": "text field is required"}, status=status.HTTP_400_BAD_REQUEST)

        ai_data = parse_expense_with_ai(text)
        if not ai_data:
            return Response({"error": "AI could not parse the text"}, status=status.HTTP_400_BAD_REQUEST)

        category_name = ai_data.get('category', 'Others')
        category, _ = Category.objects.get_or_create(name=category_name)

        expense = Expense.objects.create(
            user=request.user,
            item=ai_data.get('item', 'Miscellaneous'),
            amount=ai_data.get('amount', 0),
            category=category,
            raw_text=text
        )

        serializer = self.get_serializer(expense)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AISavingsAdviceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get AI savings advice based on current month's spending.
        """
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
            return Response({'advice': "No expenses recorded this month yet! Add some expenses to get advice."})
            
        advice = get_ai_budget_advice(summary)
        return Response({'advice': advice})
