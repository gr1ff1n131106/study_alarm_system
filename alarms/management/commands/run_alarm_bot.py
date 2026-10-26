import time
import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.core.management.base import BaseCommand
from alarms.scheduler import check_and_trigger_alarms
from alarms.telegram_service import process_incoming_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs the Study Alarm Scheduler and Telegram Bot Polling service."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting Anna's Study Alarm System & Telegram Bot..."))

        # 1. Initialize APScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            check_and_trigger_alarms,
            "interval",
            seconds=30,
            id="study_alarm_checker",
            replace_existing=True,
        )
        scheduler.start()
        self.stdout.write(self.style.SUCCESS("⏰ Alarm scheduler started (checking every 30 seconds)."))

        # 2. Telegram Long Polling Loop
        offset = None
        base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
        self.stdout.write(self.style.SUCCESS("🤖 Telegram Bot listener active. Waiting for messages..."))
        self.stdout.write(self.style.NOTICE("👉 Open Telegram, search @Alam_study_bot and send /start to connect!"))

        try:
            while True:
                params = {"timeout": 20}
                if offset:
                    params["offset"] = offset

                try:
                    resp = requests.get(base_url, params=params, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ok"):
                            for update in data.get("result", []):
                                offset = update["update_id"] + 1
                                process_incoming_update(update)
                    else:
                        time.sleep(2)
                except requests.RequestException as e:
                    self.stdout.write(self.style.WARNING(f"Network error in bot loop: {e}"))
                    time.sleep(3)
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("Stopping scheduler and bot listener..."))
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS("Shutdown complete."))
