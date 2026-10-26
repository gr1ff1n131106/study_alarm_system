import logging
import requests
from django.conf import settings
from django.utils import timezone
from alarms.models import BotSubscriber, StudySlot, ChallengeCountdown, AlarmSession

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


def send_telegram_message(chat_id, text, reply_markup=None, disable_notification=False):
    """Sends a Telegram message with Markdown formatting and optional inline keyboard."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": disable_notification,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"Error sending Telegram message to {chat_id}: {e}")
        return {"ok": False, "description": str(e)}


def answer_callback_query(callback_query_id, text=""):
    """Answers an inline keyboard button click."""
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_query_id, "text": text}, timeout=10)
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")


def send_alarm_to_all(slot, alarm_number, challenge_day=None):
    """
    Sends an alarm (1/3, 2/3, or 3/3) to all active subscribers for the given study slot.
    """
    subscribers = BotSubscriber.objects.filter(is_active=True)
    if not subscribers.exists():
        logger.warning("No active Telegram subscribers registered! Cannot send alarm.")
        return 0

    # Build message content
    day_str = f"Day {challenge_day.day_number} of 65" if challenge_day else "Safe Study Challenge"
    time_str = f"{slot.start_time.strftime('%I:%M %p')} – {slot.end_time.strftime('%I:%M %p')}"

    if alarm_number == 1:
        header = "🚨 *[ALARM 1/3] TIME FOR STUDY!*"
        body = (
            f"🎯 *Subject:* {slot.name}\n"
            f"⏰ *Slot:* {time_str}\n"
            f"📅 *Challenge:* {day_str}\n\n"
            f"💡 *Notes:* {slot.notes or 'Stay focused and avoid distractions!'}\n\n"
            f"👇 *Click below to confirm you are at your desk!*"
        )
    elif alarm_number == 2:
        header = "⚠️ *[ALARM 2/3] SECOND CALL - TIME IS TICKING!*"
        body = (
            f"⏳ *{slot.name}* has started!\n"
            f"⏰ *Slot:* {time_str}\n"
            f"📅 *Challenge:* {day_str}\n\n"
            f"You haven't acknowledged yet. Please open your books/laptop and tap below!"
        )
    else:
        header = "🔥 *[ALARM 3/3] FINAL WARNING! WAKE UP & STUDY!*"
        body = (
            f"🚨 *Don't break your study challenge streak!*\n"
            f"📚 *Class:* {slot.name} ({time_str})\n"
            f"📅 *{day_str}*\n\n"
            f"Get to work now! Every day counts towards your goal!"
        )

    full_message = f"{header}\n\n{body}"

    # Inline button for acknowledgment
    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": f"✅ I'm Ready & Studying! (Stop Alarm)",
                    "callback_data": f"ack_{slot.id}",
                }
            ]
        ]
    }

    sent_count = 0
    for sub in subscribers:
        res = send_telegram_message(sub.chat_id, full_message, reply_markup=reply_markup)
        if res.get("ok"):
            sent_count += 1

    return sent_count


def process_incoming_update(update):
    """Processes incoming messages and button callbacks from Telegram."""
    # 1. Handle Inline Button Clicks
    if "callback_query" in update:
        cb = update["callback_query"]
        cb_id = cb["id"]
        data = cb.get("data", "")
        from_user = cb.get("from", {})
        chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
        user_name = from_user.get("first_name", "Anna")

        if data.startswith("ack_"):
            slot_id = int(data.split("_")[1])
            today = timezone.localdate()
            try:
                slot = StudySlot.objects.get(id=slot_id)
                session, _ = AlarmSession.objects.get_or_create(slot=slot, date=today)
                if not session.is_acknowledged:
                    session.is_acknowledged = True
                    session.acknowledged_at = timezone.now()
                    subscriber = BotSubscriber.objects.filter(chat_id=chat_id).first()
                    session.acknowledged_by = subscriber
                    session.save()

                    answer_callback_query(cb_id, text="Study session confirmed! Good job! 🚀")
                    send_telegram_message(
                        chat_id,
                        f"🎉 *Awesome work, {user_name}!* \n\n"
                        f"Session *{slot.name}* marked as acknowledged. "
                        f"Remaining alarms are canceled. Stay focused until {slot.end_time.strftime('%I:%M %p')}! 💪"
                    )
                else:
                    answer_callback_query(cb_id, text="Already confirmed!")
            except StudySlot.DoesNotExist:
                answer_callback_query(cb_id, text="Slot not found.")
        return

    # 2. Handle Text Messages
    if "message" in update:
        msg = update["message"]
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = msg.get("text", "").strip()
        from_user = msg.get("from", {})
        first_name = from_user.get("first_name", "")
        username = from_user.get("username", "")

        if text.startswith("/start"):
            sub, created = BotSubscriber.objects.update_or_create(
                chat_id=chat_id,
                defaults={
                    "first_name": first_name,
                    "username": username,
                    "is_active": True,
                },
            )
            welcome_msg = (
                f"👋 *Welcome to Anna's Study Alarm System, {first_name or 'there'}!*\n\n"
                f"✅ Your Telegram is now connected for the **65-Day Safe Study Challenge**.\n\n"
                f"⏰ **Alarm Behavior:** When each study session begins, I will ring **3 times** until you tap the confirmation button.\n\n"
                f"📌 *Commands Available:*\n"
                f"• `/today` - View today's schedule & challenge countdown\n"
                f"• `/test` - Trigger an immediate test alarm\n"
                f"• `/help` - View schedule guidelines & tips"
            )
            send_telegram_message(chat_id, welcome_msg)

        elif text.startswith("/today"):
            today = timezone.localdate()
            countdown = ChallengeCountdown.objects.filter(date=today).first()
            day_title = f"🌟 *Day {countdown.day_number} of 65*" if countdown else f"📅 *{today.strftime('%A, %d %b %Y')}*"
            
            slots = StudySlot.objects.filter(is_active=True).order_by("start_time")
            schedule_lines = []
            for s in slots:
                if s.active_on_weekday(today.weekday()):
                    schedule_lines.append(f"• `{s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}`: *{s.name}*")

            if not schedule_lines:
                schedule_lines.append("No scheduled classes for today! Enjoy your rest/weekend.")

            resp = (
                f"📋 *Today's Study Schedule*\n"
                f"{day_title}\n\n" +
                "\n".join(schedule_lines) +
                f"\n\n🛑 *Important Notes:*\n"
                f"• 5:00 – 9:00 PM is reserved for dinner and rest.\n"
                f"• Stop project work at 11:00 PM to protect sleep!"
            )
            send_telegram_message(chat_id, resp)

        elif text.startswith("/test"):
            # Test alarm
            slot = StudySlot.objects.filter(is_active=True).first()
            if not slot:
                slot = StudySlot.objects.create(
                    name="Node.js class (Test)",
                    start_time=timezone.localtime().time(),
                    end_time=(timezone.localtime() + timezone.timedelta(hours=1)).time(),
                )
            today = timezone.localdate()
            countdown = ChallengeCountdown.objects.filter(date=today).first()
            send_alarm_to_all(slot, alarm_number=1, challenge_day=countdown)
            send_telegram_message(chat_id, "🔔 *Test alarm #1 sent with active confirmation button!*")

        elif text.startswith("/help"):
            help_msg = (
                f"📖 *Study Challenge Guidelines*\n\n"
                f"• Weekdays: Monday to Friday (65 Total Days)\n"
                f"• 8:00 AM – 9:30 AM: Node.js\n"
                f"• 10:00 AM – 11:15 AM: DevOps\n"
                f"• 1:30 PM – 3:00 PM: Java / Spring Boot\n"
                f"• 3:30 PM – 5:00 PM: Flutter\n"
                f"• 9:00 PM – 11:00 PM: University Project (10 PM stretch)\n\n"
                f"Type `/today` anytime to see today's agenda."
            )
            send_telegram_message(chat_id, help_msg)
