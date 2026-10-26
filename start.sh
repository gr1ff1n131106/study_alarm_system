#!/usr/bin/env bash
python manage.py run_alarm_bot &
gunicorn study_alarm.wsgi:application --bind 0.0.0.0:${PORT:-8000}
