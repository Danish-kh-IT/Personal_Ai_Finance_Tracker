from django.db import models
from django.db.models import Sum

# Create your models here.
from django.contrib.auth.models import User

# Expenses categories (e.g., Food, Transport, Bills)

class Category(models.Model):
    name = models.CharField(max_length=50,unique=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name  
      

# Main Expense Model

class Expense(models.Model):
  user=models.ForeignKey(User,on_delete=models.CASCADE)
  item=models.CharField(max_length=255) #For AI extraction 
  amount=models.DecimalField(max_digits=10,decimal_places=2) #For AI extraction 
  category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True)
  raw_text=models.TextField() #whatever user write here
  created_at=models.DateTimeField(auto_now_add=True)
  
  def __str__(self):
    return f"{self.item} - {self.amount} ({self.user.username})"

# Budget Model for Budget Alerts
class Budget(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, 
                                  help_text="Leave blank for overall budget")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'category', 'period']
        ordering = ['-created_at']
    
    def __str__(self):
        cat_name = self.category.name if self.category else "Overall"
        return f"{self.user.username} - {cat_name} ({self.period}): Rs. {self.amount}"
    
    def get_spent_amount(self):
        """Calculate spent amount for this budget period"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        
        if self.period == 'daily':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == 'weekly':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == 'monthly':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period == 'yearly':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        expenses = Expense.objects.filter(
            user=self.user,
            created_at__gte=start_date
        )
        
        if self.category:
            expenses = expenses.filter(category=self.category)
        
        return expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    def get_remaining_amount(self):
        """Calculate remaining budget"""
        spent = self.get_spent_amount()
        return float(self.amount) - float(spent)
    
    def get_percentage_used(self):
        """Calculate percentage of budget used"""
        spent = self.get_spent_amount()
        if float(self.amount) == 0:
            return 0
        return (float(spent) / float(self.amount)) * 100
    
    def is_exceeded(self):
        """Check if budget is exceeded"""
        return self.get_spent_amount() > self.amount