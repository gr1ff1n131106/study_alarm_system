from django.contrib import admin
from django.urls import path
from alarms.views import (
    dashboard_view,
    trigger_test_alarm_view,
    health_check_view,
    favicon_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('health/', health_check_view, name='health_check'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('test-alarm/<int:slot_id>/', trigger_test_alarm_view, name='test_alarm'),
]
