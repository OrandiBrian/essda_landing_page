from django.contrib import admin
from django.utils.html import format_html
from .models import Contribution, CampMeetingSettings

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'phone_number',
        'mpesa_transaction_id',
        'amount_formatted',
        'status_badge',
        'is_verified',
        'created_at'
    ]
    list_filter = ['status', 'is_verified', 'created_at']
    search_fields = ['full_name', 'phone_number', 'mpesa_transaction_id']
    list_editable = ['is_verified']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contributor Information', {
            'fields': ('full_name', 'phone_number')
        }),
        ('Payment Details', {
            'fields': ('amount', 'status', 'mpesa_transaction_id', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_formatted(self, obj):
        return f"Ksh. {obj.amount:,.2f}"
    amount_formatted.short_description = "Amount"
    amount_formatted.admin_order_field = "amount"
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(CampMeetingSettings)
class CampMeetingSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'target_amount_formatted',
        'event_start_date',
        'event_end_date',
        'is_active',
        'updated_at'
    ]
    
    fieldsets = (
        ('Event Settings', {
            'fields': ('target_amount', 'event_start_date', 'event_end_date', 'is_active')
        }),
        ('Payment Settings', {
            'fields': ('paybill_number', 'account_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def target_amount_formatted(self, obj):
        return f"Ksh. {obj.target_amount:,.2f}"
    target_amount_formatted.short_description = "Target Amount"
    target_amount_formatted.admin_order_field = "target_amount"
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return not CampMeetingSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False