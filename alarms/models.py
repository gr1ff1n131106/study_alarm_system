from django.db import models
from django.utils import timezone


class BotSubscriber(models.Model):
    chat_id = models.CharField(max_length=64, unique=True, help_text="Telegram Chat ID")
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name or self.username or self.chat_id} ({self.chat_id})"


class StudySlot(models.Model):
    name = models.CharField(max_length=200, help_text="e.g. Node.js class")
    start_time = models.TimeField(help_text="Format: HH:MM:SS")
    end_time = models.TimeField(help_text="Format: HH:MM:SS")
    # Days of week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    days_of_week = models.CharField(
        max_length=50,
        default="0,1,2,3,4",
        help_text="Comma-separated weekday numbers (0=Mon, 4=Fri)",
    )
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["start_time", "order"]

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"

    def active_on_weekday(self, weekday_int):
        active_days = [int(x.strip()) for x in self.days_of_week.split(",") if x.strip().isdigit()]
        return weekday_int in active_days


class ChallengeCountdown(models.Model):
    day_number = models.IntegerField(unique=True, help_text="Day 1 to 65")
    date = models.DateField(unique=True)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["day_number"]

    def __str__(self):
        return f"Day {self.day_number}: {self.date.strftime('%d %b %Y')}"


class AlarmSession(models.Model):
    """Tracks alarm states for a specific slot on a specific date."""
    slot = models.ForeignKey(StudySlot, on_delete=models.CASCADE, related_name="alarm_sessions")
    date = models.DateField(default=timezone.localdate)
    alarms_sent = models.IntegerField(default=0, help_text="Number of alarms sent so far (up to 3)")
    last_alarm_sent_at = models.DateTimeField(null=True, blank=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(BotSubscriber, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("slot", "date")

    def __str__(self):
        status = "✅ Acknowledged" if self.is_acknowledged else f"Sent {self.alarms_sent}/3"
        return f"{self.slot.name} on {self.date} - {status}"
