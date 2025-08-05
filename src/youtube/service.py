"""
YouTube data service for fetching and storing channel and video data
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import json

from .api import YouTubeAPI
from ..database import get_db_session, Channel, DailyStats, Video, VideoDailyStats
from ..config import config

logger = logging.getLogger(__name__)


class YouTubeDataService:
    """Service for managing YouTube data operations"""
    
    def __init__(self):
        """Initialize the YouTube data service"""
        self.api = YouTubeAPI()
    
    def fetch_and_store_channel_data(self, channel_id: str) -> Optional[Channel]:
        """
        Fetch channel data from YouTube API and store in database
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Channel object if successful, None otherwise
        """
        try:
            # Fetch channel info from API
            channel_data = self.api.get_channel_info(channel_id)
            if not channel_data:
                logger.error(f"Failed to fetch channel data for {channel_id}")
                return None
            
            with get_db_session() as session:
                # Check if channel already exists
                existing_channel = session.query(Channel).filter(
                    Channel.channel_id == channel_id
                ).first()
                
                if existing_channel:
                    # Update existing channel
                    for key, value in channel_data.items():
                        if key != 'channel_id' and hasattr(existing_channel, key):
                            setattr(existing_channel, key, value)
                    existing_channel.updated_at = datetime.utcnow()
                    channel = existing_channel
                    logger.info(f"Updated existing channel: {channel_id}")
                else:
                    # Create new channel
                    channel = Channel(**channel_data)
                    session.add(channel)
                    logger.info(f"Created new channel: {channel_id}")
                
                session.commit()
                return channel
                
        except Exception as e:
            logger.error(f"Error fetching and storing channel data for {channel_id}: {e}")
            return None
    
    def fetch_and_store_video_data(self, channel_id: str, max_videos: int = 50) -> List[Video]:
        """
        Fetch video data for a channel and store in database
        
        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos to fetch
            
        Returns:
            List of Video objects
        """
        try:
            # Fetch videos from API
            videos_data = self.api.get_channel_videos(channel_id, max_videos)
            if not videos_data:
                logger.warning(f"No videos found for channel {channel_id}")
                return []
            
            with get_db_session() as session:
                # Get channel from database
                channel = session.query(Channel).filter(
                    Channel.channel_id == channel_id
                ).first()
                
                if not channel:
                    logger.error(f"Channel {channel_id} not found in database")
                    return []
                
                stored_videos = []
                for video_data in videos_data:
                    # Check if video already exists
                    existing_video = session.query(Video).filter(
                        Video.video_id == video_data['video_id']
                    ).first()
                    
                    if existing_video:
                        # Update existing video
                        for key, value in video_data.items():
                            if key != 'video_id' and hasattr(existing_video, key):
                                if key == 'tags':
                                    value = json.dumps(value) if value else None
                                setattr(existing_video, key, value)
                        existing_video.updated_at = datetime.utcnow()
                        stored_videos.append(existing_video)
                    else:
                        # Create new video
                        video_data['channel_id'] = channel.id
                        if video_data.get('tags'):
                            video_data['tags'] = json.dumps(video_data['tags'])
                        video = Video(**video_data)
                        session.add(video)
                        stored_videos.append(video)
                
                session.commit()
                logger.info(f"Stored {len(stored_videos)} videos for channel {channel_id}")
                return stored_videos
                
        except Exception as e:
            logger.error(f"Error fetching and storing video data for {channel_id}: {e}")
            return []
    
    def update_daily_statistics(self, channel_id: str) -> Optional[DailyStats]:
        """
        Update daily statistics for a channel
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            DailyStats object if successful, None otherwise
        """
        try:
            today = datetime.utcnow().date()
            
            with get_db_session() as session:
                # Get channel from database
                channel = session.query(Channel).filter(
                    Channel.channel_id == channel_id
                ).first()
                
                if not channel:
                    logger.error(f"Channel {channel_id} not found in database")
                    return None
                
                # Check if stats already exist for today
                existing_stats = session.query(DailyStats).filter(
                    DailyStats.channel_id == channel.id,
                    DailyStats.date >= today
                ).first()
                
                if existing_stats:
                    logger.info(f"Daily stats already exist for {channel_id} on {today}")
                    return existing_stats
                
                # Get current channel statistics
                channel_stats = self.api.get_channel_statistics([channel_id])
                if not channel_stats:
                    logger.error(f"Failed to fetch channel statistics for {channel_id}")
                    return None
                
                current_stats = channel_stats[0]
                
                # Get recent videos and their statistics
                videos = session.query(Video).filter(
                    Video.channel_id == channel.id
                ).order_by(Video.published_at.desc()).limit(10).all()
                
                total_views = sum(video.view_count for video in videos)
                total_likes = sum(video.like_count for video in videos)
                total_comments = sum(video.comment_count for video in videos)
                
                # Get previous day's stats for growth calculation
                yesterday = today - timedelta(days=1)
                previous_stats = session.query(DailyStats).filter(
                    DailyStats.channel_id == channel.id,
                    DailyStats.date == yesterday
                ).first()
                
                # Calculate growth percentages
                views_growth = None
                likes_growth = None
                comments_growth = None
                
                if previous_stats:
                    if previous_stats.total_views > 0:
                        views_growth = ((total_views - previous_stats.total_views) / previous_stats.total_views) * 100
                    if previous_stats.total_likes > 0:
                        likes_growth = ((total_likes - previous_stats.total_likes) / previous_stats.total_likes) * 100
                    if previous_stats.total_comments > 0:
                        comments_growth = ((total_comments - previous_stats.total_comments) / previous_stats.total_comments) * 100
                
                # Create daily stats
                daily_stats = DailyStats(
                    channel_id=channel.id,
                    date=today,
                    subscriber_count=current_stats['subscriber_count'],
                    view_count=current_stats['view_count'],
                    video_count=current_stats['video_count'],
                    total_views=total_views,
                    total_likes=total_likes,
                    total_comments=total_comments,
                    views_growth=views_growth,
                    likes_growth=likes_growth,
                    comments_growth=comments_growth,
                )
                
                session.add(daily_stats)
                session.commit()
                
                logger.info(f"Updated daily statistics for {channel_id}")
                return daily_stats
                
        except Exception as e:
            logger.error(f"Error updating daily statistics for {channel_id}: {e}")
            return None
    
    def update_video_daily_statistics(self, video_id: str) -> Optional[VideoDailyStats]:
        """
        Update daily statistics for a specific video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            VideoDailyStats object if successful, None otherwise
        """
        try:
            today = datetime.utcnow().date()
            
            with get_db_session() as session:
                # Get video from database
                video = session.query(Video).filter(
                    Video.video_id == video_id
                ).first()
                
                if not video:
                    logger.error(f"Video {video_id} not found in database")
                    return None
                
                # Check if stats already exist for today
                existing_stats = session.query(VideoDailyStats).filter(
                    VideoDailyStats.video_id == video.id,
                    VideoDailyStats.date >= today
                ).first()
                
                if existing_stats:
                    logger.info(f"Video daily stats already exist for {video_id} on {today}")
                    return existing_stats
                
                # Get current video statistics
                video_stats = self.api.get_video_statistics([video_id])
                if not video_stats:
                    logger.error(f"Failed to fetch video statistics for {video_id}")
                    return None
                
                current_stats = video_stats[0]
                
                # Get previous day's stats for growth calculation
                yesterday = today - timedelta(days=1)
                previous_stats = session.query(VideoDailyStats).filter(
                    VideoDailyStats.video_id == video.id,
                    VideoDailyStats.date == yesterday
                ).first()
                
                # Calculate growth percentages
                views_growth = None
                likes_growth = None
                comments_growth = None
                
                if previous_stats:
                    if previous_stats.view_count > 0:
                        views_growth = ((current_stats['view_count'] - previous_stats.view_count) / previous_stats.view_count) * 100
                    if previous_stats.like_count > 0:
                        likes_growth = ((current_stats['like_count'] - previous_stats.like_count) / previous_stats.like_count) * 100
                    if previous_stats.comment_count > 0:
                        comments_growth = ((current_stats['comment_count'] - previous_stats.comment_count) / previous_stats.comment_count) * 100
                
                # Create video daily stats
                video_daily_stats = VideoDailyStats(
                    video_id=video.id,
                    date=today,
                    view_count=current_stats['view_count'],
                    like_count=current_stats['like_count'],
                    comment_count=current_stats['comment_count'],
                    views_growth=views_growth,
                    likes_growth=likes_growth,
                    comments_growth=comments_growth,
                )
                
                session.add(video_daily_stats)
                session.commit()
                
                logger.info(f"Updated video daily statistics for {video_id}")
                return video_daily_stats
                
        except Exception as e:
            logger.error(f"Error updating video daily statistics for {video_id}: {e}")
            return None
    
    def process_channel_data(self, channel_id: str) -> bool:
        """
        Complete data processing for a channel (fetch and store all data)
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Processing data for channel: {channel_id}")
            
            # Fetch and store channel data
            channel = self.fetch_and_store_channel_data(channel_id)
            if not channel:
                return False
            
            # Fetch and store video data
            videos = self.fetch_and_store_video_data(channel_id)
            
            # Update daily statistics
            daily_stats = self.update_daily_statistics(channel_id)
            
            # Update video daily statistics
            for video in videos:
                self.update_video_daily_statistics(video.video_id)
            
            logger.info(f"Successfully processed data for channel: {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing channel data for {channel_id}: {e}")
            return False 