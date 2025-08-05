"""
YouTube API client for fetching channel and video data
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import config

logger = logging.getLogger(__name__)


class YouTubeAPI:
    """YouTube Data API v3 client"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube API client"""
        self.api_key = api_key or config.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YouTube API key is required")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        logger.info("YouTube API client initialized")
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by channel ID
        
        Args:
            channel_id: YouTube channel ID (e.g., 'UC...')
            
        Returns:
            Channel information dictionary or None if not found
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.warning(f"Channel not found: {channel_id}")
                return None
            
            channel = response['items'][0]
            snippet = channel.get('snippet', {})
            statistics = channel.get('statistics', {})
            
            return {
                'channel_id': channel_id,
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'custom_url': snippet.get('customUrl'),
                'published_at': snippet.get('publishedAt'),
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'view_count': int(statistics.get('viewCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
            }
            
        except HttpError as e:
            logger.error(f"Error fetching channel info for {channel_id}: {e}")
            return None
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent videos from a channel
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch (default: 50)
            
        Returns:
            List of video information dictionaries
        """
        try:
            # First, get the channel's uploads playlist
            request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.warning(f"Channel not found: {channel_id}")
                return []
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            request = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                snippet = item['snippet']
                video_id = snippet['resourceId']['videoId']
                
                # Get detailed video information
                video_info = self.get_video_info(video_id)
                if video_info:
                    videos.append(video_info)
            
            return videos
            
        except HttpError as e:
            logger.error(f"Error fetching videos for channel {channel_id}: {e}")
            return []
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed video information
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video information dictionary or None if not found
        """
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.warning(f"Video not found: {video_id}")
                return None
            
            video = response['items'][0]
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            content_details = video.get('contentDetails', {})
            
            return {
                'video_id': video_id,
                'channel_id': snippet.get('channelId'),
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'published_at': snippet.get('publishedAt'),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'duration': content_details.get('duration'),
                'category_id': snippet.get('categoryId'),
                'tags': snippet.get('tags', []),
            }
            
        except HttpError as e:
            logger.error(f"Error fetching video info for {video_id}: {e}")
            return None
    
    def get_video_statistics(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get statistics for multiple videos
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            List of video statistics dictionaries
        """
        if not video_ids:
            return []
        
        try:
            # YouTube API allows up to 50 video IDs per request
            batch_size = 50
            all_statistics = []
            
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                request = self.youtube.videos().list(
                    part='statistics',
                    id=','.join(batch_ids)
                )
                response = request.execute()
                
                for video in response.get('items', []):
                    statistics = video.get('statistics', {})
                    all_statistics.append({
                        'video_id': video['id'],
                        'view_count': int(statistics.get('viewCount', 0)),
                        'like_count': int(statistics.get('likeCount', 0)),
                        'comment_count': int(statistics.get('commentCount', 0)),
                    })
            
            return all_statistics
            
        except HttpError as e:
            logger.error(f"Error fetching video statistics: {e}")
            return []
    
    def search_channels(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for YouTube channels
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of channel information dictionaries
        """
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='channel',
                maxResults=max_results
            )
            response = request.execute()
            
            channels = []
            for item in response.get('items', []):
                channel_id = item['id']['channelId']
                channel_info = self.get_channel_info(channel_id)
                if channel_info:
                    channels.append(channel_info)
            
            return channels
            
        except HttpError as e:
            logger.error(f"Error searching channels for '{query}': {e}")
            return []
    
    def get_channel_statistics(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get statistics for multiple channels
        
        Args:
            channel_ids: List of YouTube channel IDs
            
        Returns:
            List of channel statistics dictionaries
        """
        if not channel_ids:
            return []
        
        try:
            # YouTube API allows up to 50 channel IDs per request
            batch_size = 50
            all_statistics = []
            
            for i in range(0, len(channel_ids), batch_size):
                batch_ids = channel_ids[i:i + batch_size]
                
                request = self.youtube.channels().list(
                    part='statistics',
                    id=','.join(batch_ids)
                )
                response = request.execute()
                
                for channel in response.get('items', []):
                    statistics = channel.get('statistics', {})
                    all_statistics.append({
                        'channel_id': channel['id'],
                        'subscriber_count': int(statistics.get('subscriberCount', 0)),
                        'view_count': int(statistics.get('viewCount', 0)),
                        'video_count': int(statistics.get('videoCount', 0)),
                    })
            
            return all_statistics
            
        except HttpError as e:
            logger.error(f"Error fetching channel statistics: {e}")
            return [] 