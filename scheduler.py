import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import database
import time
import random
from scraper import feed_analyzer
from ai_engine import kilo_client
from platforms import reddit_client, linkedin_client, threads_client
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def daily_agent_job():
    """The main automated workflow that runs daily."""
    config = database.get_config()
    
    # --- Human Jitter ---
    jitter_max = config.get('jitter_minutes', 15) * 60 # seconds
    if jitter_max > 0:
        actual_jitter = random.randint(0, jitter_max)
        logger.info(f"Jittering start time by {actual_jitter // 60}m {actual_jitter % 60}s for human-like behavior...")
        time.sleep(actual_jitter)
    # ------------------

    # 1. Scrape Trends
    logger.info("Scraping trends from active platforms...")
    trends_found = feed_analyzer.collect_daily_trends()
    logger.info(f"Trends found: {trends_found}")
    
    # Get the latest trends to inform the AI
    recent_trends = feed_analyzer.get_recent_trends()

    # Define posting map
    platform_post_funcs = {
        'reddit': reddit_client.post,
        'linkedin': linkedin_client.post,
        'threads': threads_client.post
    }

    # 2. Generate and Post for each active platform
    for platform, post_func in platform_post_funcs.items():
        account = database.get_account(platform)
        if account and account.get('status') == 'active':
            logger.info(f"Generating post for {platform}...")
            
            # Request AI to generate post
            result = kilo_client.generate_post(platform, recent_trends)
            content = result['content']
            usage = result['usage']
            model_used = result['model']
            
            logger.info(f"Drafted post for {platform}, attempting API dispatch...")
            
            # Dispatch to platform
            if platform == 'reddit':
                success, msg = post_func(content, target_subreddit='test')
            else:
                success, msg = post_func(content)
                
            status = 'success' if success else 'failed'
            logger.info(f"{platform} Status: {status}. Msg: {msg}")
            
            # 3. Log to History with metadata
            conn = database.get_db_connection()
            conn.execute('''
                INSERT INTO post_history (platform, content, status, timestamp, prompt_tokens, completion_tokens, model_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (platform, content, status, datetime.now(), usage['prompt_tokens'], usage['completion_tokens'], model_used))
            conn.commit()
            conn.close()

    logger.info("Daily Agent Job Completed.")


def start_scheduler():
    """Initializes and starts the APScheduler with configured time."""
    if scheduler.running:
        return
        
    config = database.get_config()
    posting_time = config.get('posting_time', '09:00')
    try:
        hour, minute = map(int, posting_time.split(':'))
    except Exception:
        hour, minute = 9, 0
        
    # Schedule the job
    scheduler.add_job(
        func=daily_agent_job,
        trigger=CronTrigger(hour=hour, minute=minute),
        id='daily_post_job',
        name='Daily Social Media Automation',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduler started. Next run at {hour:02d}:{minute:02d}.")

def update_schedule_time(posting_time: str):
    """Updates the job's schedule when UI settings change."""
    try:
        hour, minute = map(int, posting_time.split(':'))
        scheduler.reschedule_job('daily_post_job', trigger=CronTrigger(hour=hour, minute=minute))
        logger.info(f"Job rescheduled to {posting_time}.")
    except Exception as e:
        logger.error(f"Failed to reschedule job: {e}")
