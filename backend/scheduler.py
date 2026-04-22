from apscheduler.schedulers.background import BackgroundScheduler
from pipeline import run_pipeline

scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler to run pipeline every 6 hours"""
    scheduler.add_job(
        run_pipeline,
        'interval',
        hours=6,
        id='pipeline_job',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started - pipeline will run every 6 hours")

def stop_scheduler():
    """Stop the background scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped")
