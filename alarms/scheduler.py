import logging
from datetime import datetime, timedelta
from django.utils import timezone
from alarms.models import StudySlot, ChallengeCountdown, AlarmSession, BotSubscriber
from alarms.telegram_service import send_alarm_to_all, send_telegram_message

logger = logging.getLogger(__name__)


def check_and_trigger_alarms():
    """
    Called every 30-60 seconds.
    Checks all active study slots for today and triggers the 3-alarm sequence:
      - Alarm 1: At start time (0 min)
      - Alarm 2: +2 minutes later (if not acknowledged)
      - Alarm 3: +4 minutes later (if not acknowledged)
    """
    now = timezone.localtime()
    today = now.date()
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday

    # Find today's challenge day info
    challenge_day = ChallengeCountdown.objects.filter(date=today).first()

    slots = StudySlot.objects.filter(is_active=True)
    for slot in slots:
        if not slot.active_on_weekday(current_weekday):
            continue

        # Convert slot.start_time to a full timezone-aware datetime for today
        slot_start_dt = timezone.make_aware(
            datetime.combine(today, slot.start_time),
            timezone.get_current_timezone()
        )

        diff_seconds = (now - slot_start_dt).total_seconds()
        diff_minutes = diff_seconds / 60.0

        # Only process if session has started and it's within the first 15 minutes of the slot
        if 0 <= diff_minutes < 15:
            session, _ = AlarmSession.objects.get_or_create(
                slot=slot,
                date=today,
            )

            # If user already tapped "I'm Studying", don't send any more alarms!
            if session.is_acknowledged:
                continue

            # Alarm 1: Trigger immediately at start time (diff >= 0 and alarms_sent == 0)
            if session.alarms_sent == 0 and diff_minutes >= 0:
                logger.info(f"Triggering Alarm 1/3 for {slot.name}")
                send_alarm_to_all(slot, alarm_number=1, challenge_day=challenge_day)
                session.alarms_sent = 1
                session.last_alarm_sent_at = now
                session.save()

            # Alarm 2: Trigger after 2 minutes if still unacknowledged
            elif session.alarms_sent == 1 and diff_minutes >= 2.0:
                logger.info(f"Triggering Alarm 2/3 for {slot.name}")
                send_alarm_to_all(slot, alarm_number=2, challenge_day=challenge_day)
                session.alarms_sent = 2
                session.last_alarm_sent_at = now
                session.save()

            # Alarm 3: Trigger after 4 minutes if still unacknowledged (Final Warning)
            elif session.alarms_sent == 2 and diff_minutes >= 4.0:
                logger.info(f"Triggering Alarm 3/3 for {slot.name}")
                send_alarm_to_all(slot, alarm_number=3, challenge_day=challenge_day)
                session.alarms_sent = 3
                session.last_alarm_sent_at = now
                session.save()

    # Optional: 10:00 PM stretch reminder and 11:00 PM sleep wind-down
    if now.hour == 22 and now.minute == 0 and now.second < 30:
        subscribers = BotSubscriber.objects.filter(is_active=True)
        for sub in subscribers:
            send_telegram_message(
                sub.chat_id,
                "🧘 *5-Minute Stretch Break!* Stand up, stretch your back, drink water, and rest your eyes before the final hour."
            )

    if now.hour == 23 and now.minute == 0 and now.second < 30:
        subscribers = BotSubscriber.objects.filter(is_active=True)
        for sub in subscribers:
            send_telegram_message(
                sub.chat_id,
                "🌙 *11:00 PM - Wind Down Time!* Stop study/project work now. Sleep well to be sharp for tomorrow's 8:00 AM class!"
            )
