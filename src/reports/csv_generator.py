"""
CSV report generator for YouTube Data Tracker
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging
from pathlib import Path

from ..database import get_db_session, Channel, DailyStats, Video, VideoDailyStats
from ..config import config

logger = logging.getLogger(__name__)


class CSVReportGenerator:
    """Generate CSV reports for YouTube data"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize CSV report generator"""
        self.output_dir = output_dir or config.REPORT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CSV report generator initialized with output dir: {self.output_dir}")
    
    def generate_channel_summary_report(self, date: Optional[datetime] = None) -> str:
        """
        Generate a summary report of all channels
        
        Args:
            date: Date for the report (defaults to today)
            
        Returns:
            Path to the generated CSV file
        """
        if date is None:
            date = datetime.utcnow()
        
        try:
            with get_db_session() as session:
                # Get all channels with their latest stats
                query = session.query(Channel, DailyStats).outerjoin(
                    DailyStats, Channel.id == DailyStats.channel_id
                ).filter(
                    DailyStats.date == date.date()
                )
                
                results = query.all()
                
                if not results:
                    logger.warning(f"No channel data found for date: {date.date()}")
                    return ""
                
                # Prepare data for DataFrame
                data = []
                for channel, stats in results:
                    row = {
                        'channel_id': channel.channel_id,
                        'title': channel.title,
                        'description': channel.description,
                        'custom_url': channel.custom_url,
                        'published_at': channel.published_at,
                        'subscriber_count': stats.subscriber_count if stats else None,
                        'view_count': stats.view_count if stats else None,
                        'video_count': stats.video_count if stats else None,
                        'total_views': stats.total_views if stats else None,
                        'total_likes': stats.total_likes if stats else None,
                        'total_comments': stats.total_comments if stats else None,
                        'views_growth': stats.views_growth if stats else None,
                        'likes_growth': stats.likes_growth if stats else None,
                        'comments_growth': stats.comments_growth if stats else None,
                        'created_at': channel.created_at,
                        'updated_at': channel.updated_at,
                    }
                    data.append(row)
                
                # Create DataFrame and save to CSV
                df = pd.DataFrame(data)
                filename = f"channel_summary_{date.strftime('%Y%m%d')}.csv"
                filepath = self.output_dir / filename
                
                df.to_csv(filepath, index=False)
                logger.info(f"Channel summary report generated: {filepath}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Error generating channel summary report: {e}")
            return ""
    
    def generate_daily_stats_report(self, start_date: datetime, end_date: datetime) -> str:
        """
        Generate daily statistics report for a date range
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            Path to the generated CSV file
        """
        try:
            with get_db_session() as session:
                # Get daily stats for the date range
                query = session.query(DailyStats, Channel).join(
                    Channel, DailyStats.channel_id == Channel.id
                ).filter(
                    DailyStats.date >= start_date.date(),
                    DailyStats.date <= end_date.date()
                ).order_by(DailyStats.date.desc(), Channel.title)
                
                results = query.all()
                
                if not results:
                    logger.warning(f"No daily stats found for date range: {start_date.date()} to {end_date.date()}")
                    return ""
                
                # Prepare data for DataFrame
                data = []
                for stats, channel in results:
                    row = {
                        'date': stats.date,
                        'channel_id': channel.channel_id,
                        'channel_title': channel.title,
                        'subscriber_count': stats.subscriber_count,
                        'view_count': stats.view_count,
                        'video_count': stats.video_count,
                        'total_views': stats.total_views,
                        'total_likes': stats.total_likes,
                        'total_comments': stats.total_comments,
                        'views_growth': stats.views_growth,
                        'likes_growth': stats.likes_growth,
                        'comments_growth': stats.comments_growth,
                        'created_at': stats.created_at,
                    }
                    data.append(row)
                
                # Create DataFrame and save to CSV
                df = pd.DataFrame(data)
                filename = f"daily_stats_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                filepath = self.output_dir / filename
                
                df.to_csv(filepath, index=False)
                logger.info(f"Daily stats report generated: {filepath}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Error generating daily stats report: {e}")
            return ""
    
    def generate_video_report(self, channel_id: Optional[str] = None, date: Optional[datetime] = None) -> str:
        """
        Generate video report for channels or specific channel
        
        Args:
            channel_id: Specific channel ID (optional)
            date: Date for the report (defaults to today)
            
        Returns:
            Path to the generated CSV file
        """
        if date is None:
            date = datetime.utcnow()
        
        try:
            with get_db_session() as session:
                # Build query
                query = session.query(Video, Channel).join(
                    Channel, Video.channel_id == Channel.id
                )
                
                if channel_id:
                    query = query.filter(Channel.channel_id == channel_id)
                
                results = query.order_by(Video.published_at.desc()).all()
                
                if not results:
                    logger.warning(f"No video data found for channel: {channel_id or 'all'}")
                    return ""
                
                # Prepare data for DataFrame
                data = []
                for video, channel in results:
                    row = {
                        'video_id': video.video_id,
                        'channel_id': channel.channel_id,
                        'channel_title': channel.title,
                        'title': video.title,
                        'description': video.description,
                        'published_at': video.published_at,
                        'view_count': video.view_count,
                        'like_count': video.like_count,
                        'comment_count': video.comment_count,
                        'duration': video.duration,
                        'category_id': video.category_id,
                        'tags': video.tags,
                        'created_at': video.created_at,
                        'updated_at': video.updated_at,
                    }
                    data.append(row)
                
                # Create DataFrame and save to CSV
                df = pd.DataFrame(data)
                if channel_id:
                    filename = f"videos_{channel_id}_{date.strftime('%Y%m%d')}.csv"
                else:
                    filename = f"videos_all_{date.strftime('%Y%m%d')}.csv"
                
                filepath = self.output_dir / filename
                df.to_csv(filepath, index=False)
                logger.info(f"Video report generated: {filepath}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Error generating video report: {e}")
            return ""
    
    def generate_video_daily_stats_report(self, video_id: Optional[str] = None, 
                                        start_date: datetime = None, 
                                        end_date: datetime = None) -> str:
        """
        Generate video daily statistics report
        
        Args:
            video_id: Specific video ID (optional)
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            Path to the generated CSV file
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.utcnow()
        
        try:
            with get_db_session() as session:
                # Build query
                query = session.query(VideoDailyStats, Video, Channel).join(
                    Video, VideoDailyStats.video_id == Video.id
                ).join(
                    Channel, Video.channel_id == Channel.id
                ).filter(
                    VideoDailyStats.date >= start_date.date(),
                    VideoDailyStats.date <= end_date.date()
                )
                
                if video_id:
                    query = query.filter(Video.video_id == video_id)
                
                results = query.order_by(VideoDailyStats.date.desc(), Video.title).all()
                
                if not results:
                    logger.warning(f"No video daily stats found for the specified criteria")
                    return ""
                
                # Prepare data for DataFrame
                data = []
                for stats, video, channel in results:
                    row = {
                        'date': stats.date,
                        'video_id': video.video_id,
                        'video_title': video.title,
                        'channel_id': channel.channel_id,
                        'channel_title': channel.title,
                        'view_count': stats.view_count,
                        'like_count': stats.like_count,
                        'comment_count': stats.comment_count,
                        'views_growth': stats.views_growth,
                        'likes_growth': stats.likes_growth,
                        'comments_growth': stats.comments_growth,
                        'created_at': stats.created_at,
                    }
                    data.append(row)
                
                # Create DataFrame and save to CSV
                df = pd.DataFrame(data)
                if video_id:
                    filename = f"video_daily_stats_{video_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                else:
                    filename = f"video_daily_stats_all_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                
                filepath = self.output_dir / filename
                df.to_csv(filepath, index=False)
                logger.info(f"Video daily stats report generated: {filepath}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Error generating video daily stats report: {e}")
            return ""
    
    def generate_comprehensive_report(self, date: Optional[datetime] = None) -> Dict[str, str]:
        """
        Generate all reports for a given date
        
        Args:
            date: Date for the report (defaults to today)
            
        Returns:
            Dictionary with report file paths
        """
        if date is None:
            date = datetime.utcnow()
        
        reports = {}
        
        try:
            # Generate channel summary report
            channel_report = self.generate_channel_summary_report(date)
            if channel_report:
                reports['channel_summary'] = channel_report
            
            # Generate daily stats report (last 7 days)
            start_date = date - timedelta(days=7)
            daily_stats_report = self.generate_daily_stats_report(start_date, date)
            if daily_stats_report:
                reports['daily_stats'] = daily_stats_report
            
            # Generate video report
            video_report = self.generate_video_report(date=date)
            if video_report:
                reports['videos'] = video_report
            
            # Generate video daily stats report
            video_daily_report = self.generate_video_daily_stats_report(
                start_date=start_date, end_date=date
            )
            if video_daily_report:
                reports['video_daily_stats'] = video_daily_report
            
            logger.info(f"Comprehensive report generated with {len(reports)} files")
            return reports
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return reports 