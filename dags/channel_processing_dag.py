"""
Airflow DAG for Individual Channel Processing
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.youtube import YouTubeDataService
from src.database import get_db_session, Channel

# Default arguments for the DAG
default_args = {
    'owner': 'youtube-data-tracker',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

# Create the DAG
dag = DAG(
    'channel_processing',
    default_args=default_args,
    description='Process individual YouTube channels',
    schedule_interval='0 */6 * * *',  # Run every 6 hours
    catchup=False,
    tags=['youtube', 'channel-processing'],
)


def process_channel(channel_id: str, **context):
    """Process a specific channel (fetch data and update stats)"""
    try:
        service = YouTubeDataService()
        
        # Fetch and store channel data
        channel = service.fetch_and_store_channel_data(channel_id)
        if not channel:
            raise Exception(f"Failed to fetch channel data for {channel_id}")
        
        # Fetch and store video data
        videos = service.fetch_and_store_video_data(channel_id)
        logging.info(f"Fetched {len(videos)} videos for channel {channel_id}")
        
        # Update daily statistics
        stats = service.update_daily_statistics(channel_id)
        if stats:
            logging.info(f"Updated daily stats for channel {channel_id}")
        
        # Update video daily statistics
        for video in videos:
            try:
                service.update_video_daily_statistics(video.video_id)
            except Exception as e:
                logging.warning(f"Failed to update video stats for {video.video_id}: {e}")
        
        return f"Successfully processed channel {channel_id}"
        
    except Exception as e:
        logging.error(f"Error processing channel {channel_id}: {e}")
        raise


def get_channels_to_process(**context):
    """Get list of channels that need processing"""
    try:
        with get_db_session() as session:
            # Get all channels
            channels = session.query(Channel).all()
            channel_ids = [channel.channel_id for channel in channels]
            
            logging.info(f"Found {len(channel_ids)} channels to process")
            return channel_ids
            
    except Exception as e:
        logging.error(f"Error getting channels to process: {e}")
        raise


def create_channel_tasks(**context):
    """Dynamically create tasks for each channel"""
    try:
        channel_ids = get_channels_to_process()
        
        # Create a task for each channel
        for channel_id in channel_ids:
            task_id = f'process_channel_{channel_id.replace("-", "_")}'
            
            task = PythonOperator(
                task_id=task_id,
                python_callable=process_channel,
                op_kwargs={'channel_id': channel_id},
                dag=dag,
            )
            
            # Store the task in the context for reference
            context['task_instance'].xcom_push(
                key=f'channel_task_{channel_id}',
                value=task_id
            )
        
        return f"Created {len(channel_ids)} channel processing tasks"
        
    except Exception as e:
        logging.error(f"Error creating channel tasks: {e}")
        raise


# Create tasks for some example channels
# You can add more channels here or make it dynamic
example_channels = [
    'UCX6OQ3DkcsbYNE6H8uQQuVA',  # MrBeast
    'UC-lHJZR3Gqxm24_Vd_AJ5Yw',  # PewDiePie
    'UCq-Fj5jknLsUf-MWSy4_brA',  # T-Series
]

# Create tasks for example channels
channel_tasks = []
for channel_id in example_channels:
    task_id = f'process_channel_{channel_id.replace("-", "_")}'
    
    task = PythonOperator(
        task_id=task_id,
        python_callable=process_channel,
        op_kwargs={'channel_id': channel_id},
        dag=dag,
    )
    
    channel_tasks.append(task)

# If you want to make it dynamic, you can use this approach:
# create_tasks_task = PythonOperator(
#     task_id='create_channel_tasks',
#     python_callable=create_channel_tasks,
#     dag=dag,
# )

# Set up dependencies (all tasks can run in parallel)
# create_tasks_task >> channel_tasks 