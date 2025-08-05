#!/usr/bin/env python3
"""
Test script to verify YouTube API integration
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import config
from src.youtube import YouTubeAPI, YouTubeDataService

def test_api_connection():
    """Test YouTube API connection"""
    print("Testing YouTube API connection...")
    
    try:
        api = YouTubeAPI()
        print("✅ YouTube API client initialized successfully")
        return api
    except Exception as e:
        print(f"❌ Failed to initialize YouTube API: {e}")
        return None

def test_channel_info(api, channel_id="UCX6OQ3DkcsbYNE6H8uQQuVA"):
    """Test fetching channel information"""
    print(f"\nTesting channel info fetch for: {channel_id}")
    
    try:
        channel_info = api.get_channel_info(channel_id)
        if channel_info:
            print(f"✅ Channel found: {channel_info['title']}")
            print(f"   Subscribers: {channel_info['subscriber_count']:,}")
            print(f"   Views: {channel_info['view_count']:,}")
            print(f"   Videos: {channel_info['video_count']:,}")
            return channel_info
        else:
            print("❌ Channel not found")
            return None
    except Exception as e:
        print(f"❌ Error fetching channel info: {e}")
        return None

def test_video_fetch(api, channel_id="UCX6OQ3DkcsbYNE6H8uQQuVA"):
    """Test fetching videos from a channel"""
    print(f"\nTesting video fetch for channel: {channel_id}")
    
    try:
        videos = api.get_channel_videos(channel_id, max_results=5)
        if videos:
            print(f"✅ Found {len(videos)} videos")
            for i, video in enumerate(videos[:3], 1):
                print(f"   {i}. {video['title'][:50]}...")
                print(f"      Views: {video['view_count']:,}, Likes: {video['like_count']:,}")
            return videos
        else:
            print("❌ No videos found")
            return []
    except Exception as e:
        print(f"❌ Error fetching videos: {e}")
        return []

def test_service_initialization():
    """Test YouTube data service initialization"""
    print("\nTesting YouTube data service...")
    
    try:
        service = YouTubeDataService()
        print("✅ YouTube data service initialized successfully")
        return service
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return None

if __name__ == "__main__":
    print("YouTube Data Tracker - API Integration Test")
    print("=" * 50)
    
    # Test API connection
    api = test_api_connection()
    if not api:
        print("\n❌ API connection failed. Please check your YOUTUBE_API_KEY.")
        sys.exit(1)
    
    # Test channel info fetch
    channel_info = test_channel_info(api)
    
    # Test video fetch
    videos = test_video_fetch(api)
    
    # Test service initialization
    service = test_service_initialization()
    
    print("\n" + "=" * 50)
    if api and channel_info and videos and service:
        print("✅ All YouTube API tests passed!")
        print("\nNext steps:")
        print("1. Set up your database connection")
        print("2. Run the data processing pipeline")
        print("3. Generate reports")
    else:
        print("❌ Some tests failed. Please check your configuration.")
        sys.exit(1) 