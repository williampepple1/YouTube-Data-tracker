"""
Airflow DAG for YouTube Data Collection
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.youtube import YouTubeDataService
from src.database import get_db_session, Channel
from src.reports import CSVReportGenerator, HTMLReportGenerator

# Default arguments for the DAG
default_args = {
    'owner': 'youtube-data-tracker',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'youtube_data_collection',
    default_args=default_args,
    description='Daily YouTube data collection and processing',
    schedule_interval='0 2 * * *',  # Run daily at 2 AM
    catchup=False,
    tags=['youtube', 'data-collection'],
)


def fetch_channel_data(channel_id: str, **context):
    """Fetch and store data for a specific channel"""
    try:
        service = YouTubeDataService()
        success = service.process_channel_data(channel_id)
        
        if success:
            logging.info(f"Successfully processed data for channel {channel_id}")
            return f"Success: {channel_id}"
        else:
            logging.error(f"Failed to process data for channel {channel_id}")
            raise Exception(f"Failed to process data for channel {channel_id}")
            
    except Exception as e:
        logging.error(f"Error processing channel {channel_id}: {e}")
        raise


def update_all_channel_stats(**context):
    """Update daily statistics for all channels"""
    try:
        service = YouTubeDataService()
        
        with get_db_session() as session:
            channels = session.query(Channel).all()
            updated_count = 0
            
            for channel in channels:
                try:
                    stats = service.update_daily_statistics(channel.channel_id)
                    if stats:
                        updated_count += 1
                        logging.info(f"Updated stats for channel {channel.channel_id}")
                except Exception as e:
                    logging.error(f"Error updating stats for channel {channel.channel_id}: {e}")
            
            logging.info(f"Updated daily statistics for {updated_count} out of {len(channels)} channels")
            return f"Updated {updated_count}/{len(channels)} channels"
            
    except Exception as e:
        logging.error(f"Error updating all channel stats: {e}")
        raise


def generate_daily_reports(**context):
    """Generate daily CSV and HTML reports"""
    try:
        today = datetime.utcnow()
        
        # Generate CSV reports
        csv_generator = CSVReportGenerator()
        csv_reports = csv_generator.generate_comprehensive_report(today)
        
        # Generate HTML reports
        html_generator = HTMLReportGenerator()
        html_reports = html_generator.generate_comprehensive_html_report(today)
        
        total_reports = len(csv_reports) + len(html_reports)
        logging.info(f"Generated {total_reports} reports: {len(csv_reports)} CSV, {len(html_reports)} HTML")
        
        return f"Generated {total_reports} reports"
        
    except Exception as e:
        logging.error(f"Error generating daily reports: {e}")
        raise


def cleanup_old_reports(**context):
    """Clean up old report files (keep last 30 days)"""
    try:
        from pathlib import Path
        from src.config import config
        import glob
        
        report_dir = config.REPORT_OUTPUT_DIR
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Find old report files
        old_files = []
        for file_pattern in ['*.csv', '*.html']:
            files = glob.glob(str(report_dir / file_pattern))
            for file_path in files:
                file_path = Path(file_path)
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    old_files.append(file_path)
        
        # Delete old files
        deleted_count = 0
        for file_path in old_files:
            try:
                file_path.unlink()
                deleted_count += 1
                logging.info(f"Deleted old report: {file_path.name}")
            except Exception as e:
                logging.error(f"Error deleting {file_path}: {e}")
        
        logging.info(f"Cleanup completed: deleted {deleted_count} old report files")
        return f"Deleted {deleted_count} old files"
        
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        raise


# Define tasks
# Task 1: Update statistics for all channels
update_stats_task = PythonOperator(
    task_id='update_channel_statistics',
    python_callable=update_all_channel_stats,
    dag=dag,
)

# Task 2: Generate daily reports
generate_reports_task = PythonOperator(
    task_id='generate_daily_reports',
    python_callable=generate_daily_reports,
    dag=dag,
)

# Task 3: Clean up old reports
cleanup_task = PythonOperator(
    task_id='cleanup_old_reports',
    python_callable=cleanup_old_reports,
    dag=dag,
)

# Task dependencies
update_stats_task >> generate_reports_task >> cleanup_task 