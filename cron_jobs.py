#!/usr/bin/env python3
"""
Cron-based scheduling for YouTube Data Tracker
Alternative to Airflow for simple scheduling
"""
import sys
import os
import time
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.youtube import YouTubeDataService
from src.database import get_db_session, Channel
from src.reports import CSVReportGenerator, HTMLReportGenerator
from src.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_tracker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def daily_data_collection():
    """Daily data collection job"""
    try:
        logger.info("Starting daily data collection...")
        
        service = YouTubeDataService()
        
        # Get all channels
        with get_db_session() as session:
            channels = session.query(Channel).all()
        
        updated_count = 0
        for channel in channels:
            try:
                # Update daily statistics
                stats = service.update_daily_statistics(channel.channel_id)
                if stats:
                    updated_count += 1
                    logger.info(f"Updated stats for channel {channel.channel_id}")
            except Exception as e:
                logger.error(f"Error updating stats for channel {channel.channel_id}: {e}")
        
        logger.info(f"Daily data collection completed: {updated_count}/{len(channels)} channels updated")
        
    except Exception as e:
        logger.error(f"Error in daily data collection: {e}")


def daily_report_generation():
    """Daily report generation job"""
    try:
        logger.info("Starting daily report generation...")
        
        today = datetime.utcnow()
        
        # Generate CSV reports
        csv_generator = CSVReportGenerator()
        csv_reports = csv_generator.generate_comprehensive_report(today)
        
        # Generate HTML reports
        html_generator = HTMLReportGenerator()
        html_reports = html_generator.generate_comprehensive_html_report(today)
        
        total_reports = len(csv_reports) + len(html_reports)
        logger.info(f"Daily report generation completed: {total_reports} reports generated")
        
    except Exception as e:
        logger.error(f"Error in daily report generation: {e}")


def weekly_report_generation():
    """Weekly report generation job"""
    try:
        logger.info("Starting weekly report generation...")
        
        # Calculate date range for the past week
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Generate weekly CSV reports
        csv_generator = CSVReportGenerator()
        daily_stats_report = csv_generator.generate_daily_stats_report(start_date, end_date)
        video_daily_report = csv_generator.generate_video_daily_stats_report(
            start_date=start_date, end_date=end_date
        )
        
        # Generate weekly HTML reports
        html_generator = HTMLReportGenerator()
        html_reports = html_generator.generate_comprehensive_html_report()
        
        total_reports = len([r for r in [daily_stats_report, video_daily_report] if r]) + len(html_reports)
        logger.info(f"Weekly report generation completed: {total_reports} reports generated")
        
    except Exception as e:
        logger.error(f"Error in weekly report generation: {e}")


def cleanup_old_reports():
    """Clean up old report files"""
    try:
        logger.info("Starting cleanup of old reports...")
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        report_dir = config.REPORT_OUTPUT_DIR
        
        deleted_count = 0
        for file_pattern in ['*.csv', '*.html']:
            for file_path in report_dir.glob(file_pattern):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old report: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {e}")
        
        logger.info(f"Cleanup completed: {deleted_count} old files deleted")
        
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")


def process_specific_channels():
    """Process specific channels (run every 6 hours)"""
    try:
        logger.info("Starting specific channel processing...")
        
        # List of channels to process more frequently
        priority_channels = [
            'UCX6OQ3DkcsbYNE6H8uQQuVA',  # MrBeast
            'UC-lHJZR3Gqxm24_Vd_AJ5Yw',  # PewDiePie
            'UCq-Fj5jknLsUf-MWSy4_brA',  # T-Series
        ]
        
        service = YouTubeDataService()
        processed_count = 0
        
        for channel_id in priority_channels:
            try:
                # Fetch and store channel data
                channel = service.fetch_and_store_channel_data(channel_id)
                if channel:
                    # Fetch and store video data
                    videos = service.fetch_and_store_video_data(channel_id)
                    logger.info(f"Processed channel {channel_id}: {len(videos)} videos")
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error processing channel {channel_id}: {e}")
        
        logger.info(f"Specific channel processing completed: {processed_count} channels processed")
        
    except Exception as e:
        logger.error(f"Error in specific channel processing: {e}")


def main():
    """Main scheduling function"""
    logger.info("Starting YouTube Data Tracker cron scheduler...")
    
    # Schedule jobs
    schedule.every().day.at("02:00").do(daily_data_collection)
    schedule.every().day.at("03:00").do(daily_report_generation)
    schedule.every().monday.at("03:00").do(weekly_report_generation)
    schedule.every().day.at("04:00").do(cleanup_old_reports)
    
    # Process specific channels every 6 hours
    schedule.every(6).hours.do(process_specific_channels)
    
    logger.info("Scheduled jobs:")
    logger.info("- Daily data collection: 02:00")
    logger.info("- Daily report generation: 03:00")
    logger.info("- Weekly report generation: Monday 03:00")
    logger.info("- Cleanup old reports: 04:00")
    logger.info("- Process specific channels: Every 6 hours")
    
    # Run pending jobs immediately
    schedule.run_pending()
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


if __name__ == "__main__":
    main() 