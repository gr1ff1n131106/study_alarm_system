from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from alarms.models import StudySlot, ChallengeCountdown, AlarmSession, BotSubscriber
from alarms.telegram_service import send_alarm_to_all


def dashboard_view(request):
    now = timezone.localtime()
    today = now.date()
    current_weekday = today.weekday()

    # Countdown
    countdown = ChallengeCountdown.objects.filter(date=today).first()
    total_days = ChallengeCountdown.objects.count() or 65
    current_day_num = countdown.day_number if countdown else 1
    progress_pct = int((current_day_num / total_days) * 100)

    # Slots
    slots = StudySlot.objects.filter(is_active=True).order_by("order", "start_time")
    slots_with_status = []

    for slot in slots:
        is_today = slot.active_on_weekday(current_weekday)
        session = AlarmSession.objects.filter(slot=slot, date=today).first()
        
        status = "Upcoming"
        if not is_today:
            status = "No class today"
        elif session and session.is_acknowledged:
            status = "Acknowledged ✅"
        elif session and session.alarms_sent > 0:
            status = f"Alarms Ringing ({session.alarms_sent}/3) 🚨"
        elif now.time() >= slot.end_time:
            status = "Completed"
        elif now.time() >= slot.start_time:
            status = "In Progress"

        slots_with_status.append({
            "slot": slot,
            "is_today": is_today,
            "status": status,
            "session": session,
        })

    subscribers = BotSubscriber.objects.filter(is_active=True)

    context = {
        "today": today,
        "now": now,
        "countdown": countdown,
        "total_days": total_days,
        "progress_pct": progress_pct,
        "slots_with_status": slots_with_status,
        "subscribers": subscribers,
    }
    return render(request, "dashboard.html", context)


def trigger_test_alarm_view(request, slot_id):
    if request.method == "POST":
        try:
            slot = StudySlot.objects.get(id=slot_id)
            today = timezone.localdate()
            countdown = ChallengeCountdown.objects.filter(date=today).first()
            count = send_alarm_to_all(slot, alarm_number=1, challenge_day=countdown)
            if count > 0:
                messages.success(request, f"🔔 Sent test alarm to {count} Telegram recipient(s)!")
            else:
                messages.warning(request, "⚠️ No active Telegram subscribers yet. Open Telegram, send /start to @Alam_study_bot first!")
        except StudySlot.DoesNotExist:
            messages.error(request, "Study slot not found.")
    return redirect("dashboard")
