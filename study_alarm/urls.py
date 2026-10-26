from django.contrib import admin
from django.urls import path
from alarms.views import dashboard_view, trigger_test_alarm_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('test-alarm/<int:slot_id>/', trigger_test_alarm_view, name='test_alarm'),
]
