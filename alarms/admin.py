from django.contrib import admin
from django.utils.html import format_html
from alarms.models import BotSubscriber, StudySlot, ChallengeCountdown, AlarmSession
from alarms.telegram_service import send_alarm_to_all


@admin.register(BotSubscriber)
class BotSubscriberAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "first_name", "username", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("chat_id", "username", "first_name")


@admin.register(StudySlot)
class StudySlotAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "days_of_week", "order", "is_active")
    list_editable = ("is_active", "order")
    list_display_links = ("name",)
    actions = ["send_test_alarm_action"]

    @admin.action(description="🔔 Trigger Test Alarm to Telegram")
    def send_test_alarm_action(self, request, queryset):
        for slot in queryset:
            count = send_alarm_to_all(slot, alarm_number=1)
            self.message_user(request, f"Alarm 1 sent for '{slot.name}' to {count} subscriber(s).")


@admin.register(ChallengeCountdown)
class ChallengeCountdownAdmin(admin.ModelAdmin):
    list_display = ("day_number", "date", "weekday_name", "note")
    search_fields = ("day_number", "date", "note")
    list_filter = ("date",)

    def weekday_name(self, obj):
        return obj.date.strftime("%A")
    weekday_name.short_description = "Day of Week"


@admin.register(AlarmSession)
class AlarmSessionAdmin(admin.ModelAdmin):
    list_display = ("slot", "date", "alarms_sent", "is_acknowledged", "acknowledged_at", "acknowledged_by")
    list_filter = ("date", "is_acknowledged", "alarms_sent")
    readonly_fields = ("last_alarm_sent_at", "acknowledged_at")
