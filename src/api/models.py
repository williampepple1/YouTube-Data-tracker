"""
Pydantic models for FastAPI endpoints
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class ChannelBase(BaseModel):
    """Base channel model"""
    channel_id: str = Field(..., description="YouTube channel ID")
    title: str = Field(..., description="Channel title")
    description: Optional[str] = Field(None, description="Channel description")
    custom_url: Optional[str] = Field(None, description="Channel custom URL")
    published_at: Optional[datetime] = Field(None, description="Channel creation date")
    subscriber_count: Optional[int] = Field(None, description="Number of subscribers")
    view_count: Optional[int] = Field(None, description="Total view count")
    video_count: Optional[int] = Field(None, description="Number of videos")


class ChannelResponse(ChannelBase):
    """Channel response model"""
    id: int = Field(..., description="Database ID")
    created_at: datetime = Field(..., description="Record creation date")
    updated_at: datetime = Field(..., description="Record update date")
    
    class Config:
        from_attributes = True


class DailyStatsBase(BaseModel):
    """Base daily stats model"""
    date: date = Field(..., description="Stats date")
    subscriber_count: Optional[int] = Field(None, description="Subscriber count")
    view_count: Optional[int] = Field(None, description="View count")
    video_count: Optional[int] = Field(None, description="Video count")
    total_views: Optional[int] = Field(None, description="Total views from recent videos")
    total_likes: Optional[int] = Field(None, description="Total likes from recent videos")
    total_comments: Optional[int] = Field(None, description="Total comments from recent videos")
    views_growth: Optional[float] = Field(None, description="Views growth percentage")
    likes_growth: Optional[float] = Field(None, description="Likes growth percentage")
    comments_growth: Optional[float] = Field(None, description="Comments growth percentage")


class DailyStatsResponse(DailyStatsBase):
    """Daily stats response model"""
    id: int = Field(..., description="Database ID")
    channel_id: int = Field(..., description="Channel database ID")
    created_at: datetime = Field(..., description="Record creation date")
    
    class Config:
        from_attributes = True


class VideoBase(BaseModel):
    """Base video model"""
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    published_at: datetime = Field(..., description="Video publication date")
    view_count: int = Field(0, description="View count")
    like_count: int = Field(0, description="Like count")
    comment_count: int = Field(0, description="Comment count")
    duration: Optional[str] = Field(None, description="Video duration")
    category_id: Optional[str] = Field(None, description="Video category ID")
    tags: Optional[str] = Field(None, description="Video tags (JSON string)")


class VideoResponse(VideoBase):
    """Video response model"""
    id: int = Field(..., description="Database ID")
    channel_id: int = Field(..., description="Channel database ID")
    created_at: datetime = Field(..., description="Record creation date")
    updated_at: datetime = Field(..., description="Record update date")
    
    class Config:
        from_attributes = True


class VideoDailyStatsBase(BaseModel):
    """Base video daily stats model"""
    date: date = Field(..., description="Stats date")
    view_count: int = Field(0, description="View count")
    like_count: int = Field(0, description="Like count")
    comment_count: int = Field(0, description="Comment count")
    views_growth: Optional[float] = Field(None, description="Views growth percentage")
    likes_growth: Optional[float] = Field(None, description="Likes growth percentage")
    comments_growth: Optional[float] = Field(None, description="Comments growth percentage")


class VideoDailyStatsResponse(VideoDailyStatsBase):
    """Video daily stats response model"""
    id: int = Field(..., description="Database ID")
    video_id: int = Field(..., description="Video database ID")
    created_at: datetime = Field(..., description="Record creation date")
    
    class Config:
        from_attributes = True


class ChannelWithStats(ChannelResponse):
    """Channel with daily stats"""
    daily_stats: Optional[DailyStatsResponse] = Field(None, description="Latest daily stats")


class VideoWithStats(VideoResponse):
    """Video with daily stats"""
    daily_stats: Optional[VideoDailyStatsResponse] = Field(None, description="Latest daily stats")


class ChannelListResponse(BaseModel):
    """Channel list response"""
    channels: List[ChannelResponse] = Field(..., description="List of channels")
    total: int = Field(..., description="Total number of channels")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class VideoListResponse(BaseModel):
    """Video list response"""
    videos: List[VideoResponse] = Field(..., description="List of videos")
    total: int = Field(..., description="Total number of videos")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class DailyStatsListResponse(BaseModel):
    """Daily stats list response"""
    stats: List[DailyStatsResponse] = Field(..., description="List of daily stats")
    total: int = Field(..., description="Total number of stats")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class ChannelQueryParams(BaseModel):
    """Channel query parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term for channel title")


class VideoQueryParams(BaseModel):
    """Video query parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")
    channel_id: Optional[str] = Field(None, description="Filter by channel ID")
    search: Optional[str] = Field(None, description="Search term for video title")


class DailyStatsQueryParams(BaseModel):
    """Daily stats query parameters"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")
    channel_id: Optional[str] = Field(None, description="Filter by channel ID")
    start_date: Optional[date] = Field(None, description="Start date for stats")
    end_date: Optional[date] = Field(None, description="End date for stats")


class ChannelCreateRequest(BaseModel):
    """Channel creation request"""
    channel_id: str = Field(..., description="YouTube channel ID")


class VideoCreateRequest(BaseModel):
    """Video creation request"""
    video_id: str = Field(..., description="YouTube video ID")
    channel_id: str = Field(..., description="YouTube channel ID")


class ReportGenerateRequest(BaseModel):
    """Report generation request"""
    report_type: str = Field(..., description="Type of report (csv, html, both)")
    date: Optional[date] = Field(None, description="Date for report (defaults to today)")
    channel_id: Optional[str] = Field(None, description="Specific channel ID for detailed reports")


class ReportResponse(BaseModel):
    """Report generation response"""
    success: bool = Field(..., description="Whether report generation was successful")
    files: List[str] = Field(..., description="List of generated file paths")
    message: str = Field(..., description="Response message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status") 