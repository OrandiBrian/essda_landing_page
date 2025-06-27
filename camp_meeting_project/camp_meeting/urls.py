from django.urls import path
from . import views

app_name = 'camp_meeting'

urlpatterns = [
    path('', views.camp_meeting_landing, name='landing'),
    path('contribute/', views.initiate_mpesa_payment, name='contribute'),
    path('api/stats/', views.get_contribution_stats, name='stats'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('stk_status/', views.stk_status_view, name='stk_status'),
    path('stk-status/', views.stk_status, name='stk-status'),
    path('finance-report/', views.finance_report, name='finance_report'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]