from apscheduler.schedulers.background import BackgroundScheduler
from pipeline import run_pipeline, send_daily_digests

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        run_pipeline,
        'interval',
        hours=6,
        id='pipeline_job',
        replace_existing=True
    )

    scheduler.add_job(
        send_daily_digests,
        'cron',
        hour=8,
        minute=0,
        id='daily_digest_job',
        replace_existing=True
    )

    scheduler.start()
    print("Scheduler started")
    print("- Feed pipeline runs every 6 hours")
    print("- Daily digest job runs every day at 08:00 server time")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")
