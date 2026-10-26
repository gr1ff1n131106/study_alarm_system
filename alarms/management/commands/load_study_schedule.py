from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from alarms.models import StudySlot, ChallengeCountdown, BotSubscriber


class Command(BaseCommand):
    help = "Loads Anna's 65-Day Safe Study Challenge schedule and countdown into the database."

    def handle(self, *args, **options):
        self.stdout.write("Loading Study Slots...")
        slots_data = [
            {
                "name": "Node.js class",
                "start_time": time(8, 0),
                "end_time": time(9, 30),
                "notes": "Followed by 9:30 - 10:00 AM break (water, stretch, quick snack)",
                "order": 1,
            },
            {
                "name": "DevOps class",
                "start_time": time(10, 0),
                "end_time": time(11, 15),
                "notes": "Followed by 11:15 AM - 1:30 PM lunch and rest",
                "order": 2,
            },
            {
                "name": "Java & Spring Boot class",
                "start_time": time(13, 30),
                "end_time": time(15, 0),
                "notes": "Java class, then Spring Boot study once Java lessons are finished. Followed by 3:00 - 3:30 PM break",
                "order": 3,
            },
            {
                "name": "Flutter class",
                "start_time": time(15, 30),
                "end_time": time(17, 0),
                "notes": "Followed by 5:00 - 9:00 PM rest, dinner, and free time",
                "order": 4,
            },
            {
                "name": "University project work",
                "start_time": time(21, 0),
                "end_time": time(23, 0),
                "notes": "Includes 5-minute stretch break around 10:00 PM. Stop at 11:00 PM for wind down and sleep!",
                "order": 5,
            },
        ]

        for s in slots_data:
            obj, created = StudySlot.objects.update_or_create(
                name=s["name"],
                defaults={
                    "start_time": s["start_time"],
                    "end_time": s["end_time"],
                    "days_of_week": "0,1,2,3,4",  # Mon - Fri
                    "notes": s["notes"],
                    "is_active": True,
                    "order": s["order"],
                }
            )
            state = "Created" if created else "Updated"
            self.stdout.write(f"  [{state}] {obj}")

        self.stdout.write("Generating 65-Weekday Countdown (26 Oct 2026 to 22 Jan 2027)...")
        start_dt = date(2026, 10, 26)
        curr = start_dt
        day_counter = 1

        while day_counter <= 65:
            # Check if weekday (0=Mon, 4=Fri)
            if curr.weekday() < 5:
                note = "Day 1 — schedule begins" if day_counter == 1 else ("Final Day — Challenge Complete!" if day_counter == 65 else "")
                ChallengeCountdown.objects.update_or_create(
                    day_number=day_counter,
                    defaults={
                        "date": curr,
                        "note": note,
                    }
                )
                day_counter += 1
            curr += timedelta(days=1)

        # Pre-seed Anna's Telegram account so alarms work immediately
        BotSubscriber.objects.update_or_create(
            chat_id="1063338929",
            defaults={
                "username": "Sengchhay009",
                "first_name": "Anna",
                "is_active": True,
            }
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded all study slots, 65 countdown days, and subscriber!"))
