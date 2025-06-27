from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Contribution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(1.00)]
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    mpesa_transaction_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
    )
    is_verified = models.BooleanField(default=False)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.full_name} - Ksh. {self.amount}"
    
    @property
    def first_name(self):
        """Return the first name from full name"""
        return self.full_name.split()[0] if self.full_name else ""

class CampMeetingSettings(models.Model):
    """Settings for the camp meeting"""
    target_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=2300000.00
    )
    event_start_date = models.DateTimeField()
    event_end_date = models.DateTimeField()
    paybill_number = models.CharField(max_length=20, default="")
    account_number = models.CharField(max_length=50, default="Camp2025")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Camp Meeting Settings"
        verbose_name_plural = "Camp Meeting Settings"
    
    def __str__(self):
        return f"Camp Meeting 2025 Settings"