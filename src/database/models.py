"""
Database models for YouTube Data Tracker
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Channel(Base):
    """YouTube channel information"""
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    custom_url = Column(String(100))
    published_at = Column(DateTime)
    subscriber_count = Column(Integer)
    view_count = Column(Integer)
    video_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    daily_stats = relationship("DailyStats", back_populates="channel")
    
    def __repr__(self):
        return f"<Channel(channel_id='{self.channel_id}', title='{self.title}')>"


class DailyStats(Base):
    """Daily statistics for YouTube channels"""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Channel statistics
    subscriber_count = Column(Integer)
    view_count = Column(Integer)
    video_count = Column(Integer)
    
    # Video statistics (aggregated from recent videos)
    total_views = Column(Integer)
    total_likes = Column(Integer)
    total_comments = Column(Integer)
    
    # Calculated metrics
    views_growth = Column(Float)  # Percentage change from previous day
    likes_growth = Column(Float)
    comments_growth = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    channel = relationship("Channel", back_populates="daily_stats")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_channel_date', 'channel_id', 'date'),
        Index('idx_date', 'date'),
    )
    
    def __repr__(self):
        return f"<DailyStats(channel_id={self.channel_id}, date='{self.date.date()}')>"


class Video(Base):
    """Individual video information"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(20), unique=True, nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text)
    published_at = Column(DateTime, nullable=False)
    
    # Video statistics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Video metadata
    duration = Column(String(20))  # ISO 8601 duration format
    category_id = Column(String(50))
    tags = Column(Text)  # JSON array of tags
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Video(video_id='{self.video_id}', title='{self.title}')>"


class VideoDailyStats(Base):
    """Daily statistics for individual videos"""
    __tablename__ = "video_daily_stats"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Daily statistics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Growth metrics
    views_growth = Column(Float)
    likes_growth = Column(Float)
    comments_growth = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_video_date', 'video_id', 'date'),
        Index('idx_video_stats_date', 'date'),
    )
    
    def __repr__(self):
        return f"<VideoDailyStats(video_id={self.video_id}, date='{self.date.date()}')>" 