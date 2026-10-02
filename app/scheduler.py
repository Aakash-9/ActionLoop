from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import SessionLocal
from .reports import save_weekly_report

scheduler = BackgroundScheduler()


def _run_weekly_report():
    db = SessionLocal()
    try:
        save_weekly_report(db)
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(_run_weekly_report, CronTrigger(day_of_week="mon", hour=8))
    scheduler.start()
