"""
Airflow DAG for Weekly Report Generation
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

from src.reports import CSVReportGenerator, HTMLReportGenerator
from src.database import get_db_session, Channel, DailyStats
from src.config import config

# Default arguments for the DAG
default_args = {
    'owner': 'youtube-data-tracker',
    'depends_on_past': False,
    'start_date': days_ago(7),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'weekly_reports',
    default_args=default_args,
    description='Generate weekly YouTube analytics reports',
    schedule_interval='0 3 * * 1',  # Run every Monday at 3 AM
    catchup=False,
    tags=['youtube', 'reports', 'weekly'],
)


def generate_weekly_csv_reports(**context):
    """Generate weekly CSV reports"""
    try:
        # Calculate date range for the past week
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        csv_generator = CSVReportGenerator()
        
        # Generate daily stats report for the week
        daily_stats_report = csv_generator.generate_daily_stats_report(start_date, end_date)
        
        # Generate video daily stats report for the week
        video_daily_report = csv_generator.generate_video_daily_stats_report(
            start_date=start_date, end_date=end_date
        )
        
        reports = []
        if daily_stats_report:
            reports.append(daily_stats_report)
        if video_daily_report:
            reports.append(video_daily_report)
        
        logging.info(f"Generated {len(reports)} weekly CSV reports")
        return f"Generated {len(reports)} CSV reports"
        
    except Exception as e:
        logging.error(f"Error generating weekly CSV reports: {e}")
        raise


def generate_weekly_html_reports(**context):
    """Generate weekly HTML reports"""
    try:
        html_generator = HTMLReportGenerator()
        
        # Generate comprehensive HTML reports
        html_reports = html_generator.generate_comprehensive_html_report()
        
        logging.info(f"Generated {len(html_reports)} weekly HTML reports")
        return f"Generated {len(html_reports)} HTML reports"
        
    except Exception as e:
        logging.error(f"Error generating weekly HTML reports: {e}")
        raise


def generate_weekly_summary(**context):
    """Generate a weekly summary report"""
    try:
        from pathlib import Path
        import json
        
        # Calculate date range for the past week
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        with get_db_session() as session:
            # Get weekly statistics
            weekly_stats = session.query(DailyStats).filter(
                DailyStats.date >= start_date.date(),
                DailyStats.date <= end_date.date()
            ).all()
            
            # Calculate summary metrics
            total_channels = session.query(Channel).count()
            total_stats = len(weekly_stats)
            
            if weekly_stats:
                avg_subscribers = sum(stat.subscriber_count or 0 for stat in weekly_stats) / len(weekly_stats)
                avg_views = sum(stat.view_count or 0 for stat in weekly_stats) / len(weekly_stats)
                avg_videos = sum(stat.video_count or 0 for stat in weekly_stats) / len(weekly_stats)
            else:
                avg_subscribers = avg_views = avg_videos = 0
            
            # Create summary data
            summary = {
                'report_period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                },
                'metrics': {
                    'total_channels': total_channels,
                    'total_stats_records': total_stats,
                    'average_subscribers': round(avg_subscribers, 2),
                    'average_views': round(avg_views, 2),
                    'average_videos': round(avg_videos, 2)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Save summary to file
            summary_file = config.REPORT_OUTPUT_DIR / f"weekly_summary_{end_date.strftime('%Y%m%d')}.json"
            summary_file.write_text(json.dumps(summary, indent=2))
            
            logging.info(f"Generated weekly summary: {summary_file}")
            return f"Generated weekly summary with {total_stats} stats records"
        
    except Exception as e:
        logging.error(f"Error generating weekly summary: {e}")
        raise


def archive_weekly_reports(**context):
    """Archive weekly reports to a separate directory"""
    try:
        from pathlib import Path
        import shutil
        from datetime import datetime
        
        # Create archive directory
        archive_dir = config.REPORT_OUTPUT_DIR / "archive" / f"week_{datetime.utcnow().strftime('%Y%m%d')}"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move weekly reports to archive
        report_dir = config.REPORT_OUTPUT_DIR
        moved_count = 0
        
        for file_path in report_dir.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.csv', '.html', '.json']:
                # Check if file was created this week
                if (datetime.utcnow() - datetime.fromtimestamp(file_path.stat().st_mtime)).days <= 7:
                    shutil.move(str(file_path), str(archive_dir / file_path.name))
                    moved_count += 1
        
        logging.info(f"Archived {moved_count} weekly reports to {archive_dir}")
        return f"Archived {moved_count} reports"
        
    except Exception as e:
        logging.error(f"Error archiving weekly reports: {e}")
        raise


def send_weekly_notification(**context):
    """Send notification about weekly report completion"""
    try:
        # This is a placeholder for notification logic
        # You can integrate with email, Slack, or other notification services
        
        logging.info("Weekly reports completed successfully")
        
        # Example: Send email notification
        # from airflow.utils.email import send_email
        # send_email(
        #     to=['admin@example.com'],
        #     subject='Weekly YouTube Reports Generated',
        #     html_content='Weekly reports have been generated successfully.'
        # )
        
        return "Weekly notification sent"
        
    except Exception as e:
        logging.error(f"Error sending weekly notification: {e}")
        raise


# Define tasks
generate_csv_task = PythonOperator(
    task_id='generate_weekly_csv_reports',
    python_callable=generate_weekly_csv_reports,
    dag=dag,
)

generate_html_task = PythonOperator(
    task_id='generate_weekly_html_reports',
    python_callable=generate_weekly_html_reports,
    dag=dag,
)

generate_summary_task = PythonOperator(
    task_id='generate_weekly_summary',
    python_callable=generate_weekly_summary,
    dag=dag,
)

archive_reports_task = PythonOperator(
    task_id='archive_weekly_reports',
    python_callable=archive_weekly_reports,
    dag=dag,
)

send_notification_task = PythonOperator(
    task_id='send_weekly_notification',
    python_callable=send_weekly_notification,
    dag=dag,
)

# Task dependencies
[generate_csv_task, generate_html_task] >> generate_summary_task >> archive_reports_task >> send_notification_task 