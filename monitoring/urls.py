from django.urls import path
from . import views
app_name = 'monitoring'

urlpatterns = [
    path('dashboard/', views.dashboard_monitoraggio, name='monitoring_dashboard'),
]
