"""
FastAPI endpoints for YouTube Data Tracker
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from ..database import get_db, Channel, DailyStats, Video, VideoDailyStats
from ..youtube import YouTubeDataService
from ..reports import CSVReportGenerator, HTMLReportGenerator
from ..config import config
from .models import (
    ChannelResponse, VideoResponse, DailyStatsResponse, VideoDailyStatsResponse,
    ChannelListResponse, VideoListResponse, DailyStatsListResponse,
    ChannelCreateRequest, VideoCreateRequest, ReportGenerateRequest, ReportResponse,
    HealthResponse, ChannelQueryParams, VideoQueryParams, DailyStatsQueryParams
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="YouTube Data Tracker API",
    description="API for tracking YouTube channel and video statistics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "YouTube Data Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=db_status
    )


# Channel endpoints
@app.get("/channels", response_model=ChannelListResponse)
async def get_channels(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for channel title"),
    db: Session = Depends(get_db)
):
    """Get list of channels with pagination and search"""
    try:
        query = db.query(Channel)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Channel.title.ilike(f"%{search}%"),
                    Channel.description.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        channels = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return ChannelListResponse(
            channels=channels,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error fetching channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str, db: Session = Depends(get_db)):
    """Get specific channel by YouTube channel ID"""
    try:
        channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel with ID {channel_id} not found"
            )
        
        return channel
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    request: ChannelCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new channel by fetching data from YouTube API"""
    try:
        # Check if channel already exists
        existing_channel = db.query(Channel).filter(
            Channel.channel_id == request.channel_id
        ).first()
        
        if existing_channel:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Channel with ID {request.channel_id} already exists"
            )
        
        # Fetch and store channel data
        service = YouTubeDataService()
        channel = service.fetch_and_store_channel_data(request.channel_id)
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel with ID {request.channel_id} not found on YouTube"
            )
        
        return channel
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating channel {request.channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Video endpoints
@app.get("/videos", response_model=VideoListResponse)
async def get_videos(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    search: Optional[str] = Query(None, description="Search term for video title"),
    db: Session = Depends(get_db)
):
    """Get list of videos with pagination and filters"""
    try:
        query = db.query(Video).join(Channel)
        
        # Apply filters
        if channel_id:
            query = query.filter(Channel.channel_id == channel_id)
        
        if search:
            query = query.filter(
                or_(
                    Video.title.ilike(f"%{search}%"),
                    Video.description.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        videos = query.order_by(Video.published_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return VideoListResponse(
            videos=videos,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get specific video by YouTube video ID"""
    try:
        video = db.query(Video).filter(Video.video_id == video_id).first()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID {video_id} not found"
            )
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/videos", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
    request: VideoCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new video by fetching data from YouTube API"""
    try:
        # Check if video already exists
        existing_video = db.query(Video).filter(
            Video.video_id == request.video_id
        ).first()
        
        if existing_video:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Video with ID {request.video_id} already exists"
            )
        
        # Get channel
        channel = db.query(Channel).filter(
            Channel.channel_id == request.channel_id
        ).first()
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel with ID {request.channel_id} not found"
            )
        
        # Fetch video data from YouTube API
        service = YouTubeDataService()
        video_info = service.api.get_video_info(request.video_id)
        
        if not video_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID {request.video_id} not found on YouTube"
            )
        
        # Create video record
        video = Video(
            video_id=video_info['video_id'],
            channel_id=channel.id,
            title=video_info['title'],
            description=video_info['description'],
            published_at=video_info['published_at'],
            view_count=video_info['view_count'],
            like_count=video_info['like_count'],
            comment_count=video_info['comment_count'],
            duration=video_info['duration'],
            category_id=video_info['category_id'],
            tags=video_info.get('tags')
        )
        
        db.add(video)
        db.commit()
        db.refresh(video)
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video {request.video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Daily stats endpoints
@app.get("/stats/daily", response_model=DailyStatsListResponse)
async def get_daily_stats(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    start_date: Optional[date] = Query(None, description="Start date for stats"),
    end_date: Optional[date] = Query(None, description="End date for stats"),
    db: Session = Depends(get_db)
):
    """Get daily statistics with filters"""
    try:
        query = db.query(DailyStats).join(Channel)
        
        # Apply filters
        if channel_id:
            query = query.filter(Channel.channel_id == channel_id)
        
        if start_date:
            query = query.filter(DailyStats.date >= start_date)
        
        if end_date:
            query = query.filter(DailyStats.date <= end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        stats = query.order_by(DailyStats.date.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return DailyStatsListResponse(
            stats=stats,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error fetching daily stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/stats/daily/{channel_id}", response_model=List[DailyStatsResponse])
async def get_channel_daily_stats(
    channel_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
    db: Session = Depends(get_db)
):
    """Get daily statistics for a specific channel"""
    try:
        # Get channel
        channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel with ID {channel_id} not found"
            )
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Get stats
        stats = db.query(DailyStats).filter(
            and_(
                DailyStats.channel_id == channel.id,
                DailyStats.date >= start_date,
                DailyStats.date <= end_date
            )
        ).order_by(DailyStats.date.desc()).all()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching daily stats for channel {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Report endpoints
@app.post("/reports/generate", response_model=ReportResponse)
async def generate_reports(request: ReportGenerateRequest):
    """Generate CSV and/or HTML reports"""
    try:
        files = []
        report_date = request.date or datetime.utcnow().date()
        
        if request.report_type.lower() in ["csv", "both"]:
            csv_generator = CSVReportGenerator()
            if request.channel_id:
                # Generate channel-specific reports
                csv_files = csv_generator.generate_video_report(
                    channel_id=request.channel_id, 
                    date=datetime.combine(report_date, datetime.min.time())
                )
                if csv_files:
                    files.append(csv_files)
            else:
                # Generate comprehensive reports
                csv_reports = csv_generator.generate_comprehensive_report(
                    datetime.combine(report_date, datetime.min.time())
                )
                files.extend(csv_reports.values())
        
        if request.report_type.lower() in ["html", "both"]:
            html_generator = HTMLReportGenerator()
            if request.channel_id:
                # Generate channel-specific report
                html_file = html_generator.generate_channel_detail_report(
                    request.channel_id,
                    datetime.combine(report_date, datetime.min.time())
                )
                if html_file:
                    files.append(html_file)
            else:
                # Generate comprehensive reports
                html_reports = html_generator.generate_comprehensive_html_report(
                    datetime.combine(report_date, datetime.min.time())
                )
                files.extend(html_reports.values())
        
        if files:
            return ReportResponse(
                success=True,
                files=files,
                message=f"Generated {len(files)} report(s) successfully"
            )
        else:
            return ReportResponse(
                success=False,
                files=[],
                message="No reports were generated. Check if data exists for the specified criteria."
            )
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Data processing endpoints
@app.post("/process/channel/{channel_id}")
async def process_channel_data(channel_id: str, db: Session = Depends(get_db)):
    """Process data for a specific channel (fetch and store all data)"""
    try:
        service = YouTubeDataService()
        success = service.process_channel_data(channel_id)
        
        if success:
            return {"message": f"Successfully processed data for channel {channel_id}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process data for channel {channel_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing channel data for {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/update/stats")
async def update_all_stats(db: Session = Depends(get_db)):
    """Update daily statistics for all channels"""
    try:
        service = YouTubeDataService()
        
        # Get all channels
        channels = db.query(Channel).all()
        updated_count = 0
        
        for channel in channels:
            try:
                stats = service.update_daily_statistics(channel.channel_id)
                if stats:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error updating stats for channel {channel.channel_id}: {e}")
        
        return {
            "message": f"Updated daily statistics for {updated_count} out of {len(channels)} channels"
        }
        
    except Exception as e:
        logger.error(f"Error updating all stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 