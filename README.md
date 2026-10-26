# ⏰ Anna's Safe Study Challenge & Telegram Alarm System

A Python + Django system designed to manage and enforce your **65-Weekday Safe Study Challenge** (26 October 2026 – 22 January 2027) with an automated **3-stage Telegram Alarm Clock**.

---

## 🚀 Quick Start Guide

### 1. Connect your Telegram Account
1. Open Telegram on your phone or PC.
2. Search for the bot: **`@Alam_study_bot`**
3. Tap **Start** or send **`/start`**.
   - Your account is now subscribed to receive automated study alarms!

---

### 2. Start the Bot & Scheduler
To keep the alarm clock active and listening for your responses, run:

```powershell
cd "C:\Users\LENOVO\.gemini\antigravity\scratch\study_alarm_system"
python manage.py run_alarm_bot
```

> **What this command does:**
> - Runs the background scheduler (checks every 30 seconds).
> - Listens to Telegram messages (`/start`, `/today`, `/test`, `/help`).
> - Handles the **`✅ I'm Ready & Studying!`** button click.

---

### 3. (Optional) Run the Web Dashboard & Admin
Open a second terminal window to view the visual tracker & timetable:

```powershell
cd "C:\Users\LENOVO\.gemini\antigravity\scratch\study_alarm_system"
python manage.py runserver
```

- **Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  - **Username:** `admin`
  - **Password:** `admin123`

---

## 🔔 How the 3-Stage Alarm Works

When each study session begins, the system fires a 3-stage alarm sequence directly to your Telegram:

1. **Alarm 1/3 (At start time, e.g. 08:00 AM):**
   - Notification with session name and challenge day info.
   - Includes an interactive button: `[ ✅ I'm Ready & Studying! (Stop Alarm) ]`.
2. **Alarm 2/3 (+2 minutes later, e.g. 08:02 AM):**
   - Fires only if you haven't clicked the acknowledgment button yet.
3. **Alarm 3/3 (+4 minutes later, e.g. 08:04 AM):**
   - Final urgent warning to ensure you don't miss the study session.

👉 **As soon as you tap the confirmation button**, the remaining alarms for that session are cancelled, and a cheer message is sent.

---

## 📅 Daily Study Schedule Loaded (Mon – Fri)

| # | Time | Session / Activity | Routine Notes |
|---|---|---|---|
| 1 | **8:00 – 9:30 AM** | Node.js class | Followed by 9:30–10:00 AM break (water & quick snack) |
| 2 | **10:00 – 11:15 AM** | DevOps class | Followed by 11:15 AM–1:30 PM lunch & rest |
| 3 | **1:30 – 3:00 PM** | Java & Spring Boot class | Followed by 3:00–3:30 PM stretch break |
| 4 | **3:30 – 5:00 PM** | Flutter class | Followed by 5:00–9:00 PM rest, dinner & free time |
| 5 | **9:00 – 11:00 PM** | University project work | Includes 10:00 PM 5-min stretch; stop at 11:00 PM for sleep |
