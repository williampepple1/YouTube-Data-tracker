"""
HTML report generator for YouTube Data Tracker
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

from jinja2 import Environment, FileSystemLoader, Template
from ..database import get_db_session, Channel, DailyStats, Video, VideoDailyStats
from ..config import config

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate HTML reports for YouTube data"""
    
    def __init__(self, output_dir: Optional[Path] = None, template_dir: Optional[Path] = None):
        """Initialize HTML report generator"""
        self.output_dir = output_dir or config.REPORT_OUTPUT_DIR
        self.template_dir = template_dir or config.TEMPLATE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
        # Create default templates if they don't exist
        self._create_default_templates()
        
        logger.info(f"HTML report generator initialized with output dir: {self.output_dir}")
    
    def _create_default_templates(self):
        """Create default HTML templates"""
        base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}YouTube Data Tracker{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .growth-positive { color: #28a745; }
        .growth-negative { color: #dc3545; }
        .table-responsive { border-radius: 10px; overflow: hidden; }
        .chart-container { position: relative; height: 400px; margin: 20px 0; }
        .header-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark header-bg">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fab fa-youtube me-2"></i>YouTube Data Tracker
            </a>
            <span class="navbar-text">
                Generated on {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}
            </span>
        </div>
    </nav>

    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <footer class="bg-light text-center py-3 mt-5">
        <p class="text-muted">YouTube Data Tracker - Automated Analytics Report</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>"""
        
        dashboard_template = """{% extends "base.html" %}

{% block title %}Dashboard - {{ date.strftime('%Y-%m-%d') }}{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">
            <i class="fas fa-chart-line me-2"></i>YouTube Analytics Dashboard
        </h1>
        <p class="text-muted">Data for {{ date.strftime('%B %d, %Y') }}</p>
    </div>
</div>

<!-- Summary Metrics -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="metric-card">
            <h3>{{ total_channels }}</h3>
            <p class="mb-0">Total Channels</p>
        </div>
    </div>
    <div class="col-md-3">
        <div class="metric-card">
            <h3>{{ total_subscribers | format_number }}</h3>
            <p class="mb-0">Total Subscribers</p>
        </div>
    </div>
    <div class="col-md-3">
        <div class="metric-card">
            <h3>{{ total_views | format_number }}</h3>
            <p class="mb-0">Total Views</p>
        </div>
    </div>
    <div class="col-md-3">
        <div class="metric-card">
            <h3>{{ total_videos }}</h3>
            <p class="mb-0">Total Videos</p>
        </div>
    </div>
</div>

<!-- Charts Row -->
<div class="row mb-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-chart-bar me-2"></i>Channel Performance</h5>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="channelChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-chart-pie me-2"></i>Growth Trends</h5>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="growthChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Channel Table -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-table me-2"></i>Channel Details</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Channel</th>
                                <th>Subscribers</th>
                                <th>Views</th>
                                <th>Videos</th>
                                <th>Growth</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for channel in channels %}
                            <tr>
                                <td>
                                    <strong>{{ channel.title }}</strong><br>
                                    <small class="text-muted">{{ channel.channel_id }}</small>
                                </td>
                                <td>{{ channel.subscriber_count | format_number }}</td>
                                <td>{{ channel.view_count | format_number }}</td>
                                <td>{{ channel.video_count | format_number }}</td>
                                <td>
                                    {% if channel.views_growth %}
                                        <span class="{% if channel.views_growth > 0 %}growth-positive{% else %}growth-negative{% endif %}">
                                            <i class="fas fa-{% if channel.views_growth > 0 %}arrow-up{% else %}arrow-down{% endif %}"></i>
                                            {{ "%.1f"|format(channel.views_growth) }}%
                                        </span>
                                    {% else %}
                                        <span class="text-muted">N/A</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Channel Performance Chart
const channelCtx = document.getElementById('channelChart').getContext('2d');
new Chart(channelCtx, {
    type: 'bar',
    data: {
        labels: {{ channel_names | tojson }},
        datasets: [{
            label: 'Subscribers',
            data: {{ subscriber_counts | tojson }},
            backgroundColor: 'rgba(102, 126, 234, 0.8)',
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

// Growth Trends Chart
const growthCtx = document.getElementById('growthChart').getContext('2d');
new Chart(growthCtx, {
    type: 'line',
    data: {
        labels: {{ channel_names | tojson }},
        datasets: [{
            label: 'Views Growth (%)',
            data: {{ views_growth | tojson }},
            borderColor: 'rgba(40, 167, 69, 1)',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});
</script>
{% endblock %}"""
        
        # Write templates to files
        (self.template_dir / "base.html").write_text(base_template)
        (self.template_dir / "dashboard.html").write_text(dashboard_template)
    
    def generate_dashboard_report(self, date: Optional[datetime] = None) -> str:
        """
        Generate a comprehensive dashboard HTML report
        
        Args:
            date: Date for the report (defaults to today)
            
        Returns:
            Path to the generated HTML file
        """
        if date is None:
            date = datetime.utcnow()
        
        try:
            with get_db_session() as session:
                # Get channel data with latest stats
                query = session.query(Channel, DailyStats).outerjoin(
                    DailyStats, Channel.id == DailyStats.channel_id
                ).filter(
                    DailyStats.date == date.date()
                )
                
                results = query.all()
                
                if not results:
                    logger.warning(f"No channel data found for date: {date.date()}")
                    return ""
                
                # Prepare data for template
                channels = []
                channel_names = []
                subscriber_counts = []
                view_counts = []
                video_counts = []
                views_growth = []
                
                total_subscribers = 0
                total_views = 0
                total_videos = 0
                
                for channel, stats in results:
                    if stats:
                        channel_data = {
                            'channel_id': channel.channel_id,
                            'title': channel.title,
                            'subscriber_count': stats.subscriber_count or 0,
                            'view_count': stats.view_count or 0,
                            'video_count': stats.video_count or 0,
                            'views_growth': stats.views_growth or 0,
                            'likes_growth': stats.likes_growth or 0,
                            'comments_growth': stats.comments_growth or 0,
                        }
                        
                        total_subscribers += channel_data['subscriber_count']
                        total_views += channel_data['view_count']
                        total_videos += channel_data['video_count']
                        
                        channels.append(channel_data)
                        channel_names.append(channel.title[:20] + "..." if len(channel.title) > 20 else channel.title)
                        subscriber_counts.append(channel_data['subscriber_count'])
                        view_counts.append(channel_data['view_count'])
                        video_counts.append(channel_data['video_count'])
                        views_growth.append(channel_data['views_growth'])
                
                # Prepare template context
                context = {
                    'date': date,
                    'generated_at': datetime.utcnow(),
                    'total_channels': len(channels),
                    'total_subscribers': total_subscribers,
                    'total_views': total_views,
                    'total_videos': total_videos,
                    'channels': channels,
                    'channel_names': channel_names,
                    'subscriber_counts': subscriber_counts,
                    'view_counts': view_counts,
                    'video_counts': video_counts,
                    'views_growth': views_growth,
                }
                
                # Render template
                template = self.env.get_template('dashboard.html')
                html_content = template.render(**context)
                
                # Save HTML file
                filename = f"dashboard_{date.strftime('%Y%m%d')}.html"
                filepath = self.output_dir / filename
                filepath.write_text(html_content)
                
                logger.info(f"Dashboard report generated: {filepath}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Error generating dashboard report: {e}")
            return ""
    
    def generate_channel_detail_report(self, channel_id: str, date: Optional[datetime] = None) -> str:
        """
        Generate detailed HTML report for a specific channel
        
        Args:
            channel_id: YouTube channel ID
            date: Date for the report (defaults to today)
            
        Returns:
            Path to the generated HTML file
        """
        if date is None:
            date = datetime.utcnow()
        
        try:
            with get_db_session() as session:
                # Get channel and stats
                channel = session.query(Channel).filter(
                    Channel.channel_id == channel_id
                ).first()
                
                if not channel:
                    logger.error(f"Channel not found: {channel_id}")
                    return ""
                
                # Get daily stats for the last 30 days
                start_date = date - timedelta(days=30)
                daily_stats = session.query(DailyStats).filter(
                    DailyStats.channel_id == channel.id,
                    DailyStats.date >= start_date.date(),
                    DailyStats.date <= date.date()
                ).order_by(DailyStats.date).all()
                
                # Get recent videos
                videos = session.query(Video).filter(
                    Video.channel_id == channel.id
                ).order_by(Video.published_at.desc()).limit(10).all()
                
                # Prepare data for charts
                dates = [stat.date.strftime('%Y-%m-%d') for stat in daily_stats]
                subscriber_counts = [stat.subscriber_count for stat in daily_stats]
                view_counts = [stat.view_count for stat in daily_stats]
                video_counts = [stat.video_count for stat in daily_stats]
                
                # Create simple HTML report
                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Channel Report - {channel.title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container mt-4">
        <h1>{channel.title}</h1>
        <p class="text-muted">Channel ID: {channel.channel_id}</p>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Subscriber Growth</div>
                    <div class="card-body">
                        <canvas id="subscriberChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">View Growth</div>
                    <div class="card-body">
                        <canvas id="viewChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <h3>Recent Videos</h3>
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Published</th>
                            <th>Views</th>
                            <th>Likes</th>
                            <th>Comments</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{video.title}</td><td>{video.published_at.strftime("%Y-%m-%d")}</td><td>{video.view_count:,}</td><td>{video.like_count:,}</td><td>{video.comment_count:,}</td></tr>' for video in videos)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        const subscriberCtx = document.getElementById('subscriberChart').getContext('2d');
        new Chart(subscriberCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [{{
                    label: 'Subscribers',
                    data: {json.dumps(subscriber_counts)},
                    borderColor: 'rgba(102, 126, 234, 1)',
                    tension: 0.1
                }}]
            }}
        }});
        
        const viewCtx = document.getElementById('viewChart').getContext('2d');
        new Chart(viewCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [{{
                    label: 'Views',
                    data: {json.dumps(view_counts)},
                    borderColor: 'rgba(40, 167, 69, 1)',
                    tension: 0.1
                }}]
            }}
        }});
    </script>
</body>
</html>"""
                
                # Save HTML file
                filename = f"channel_{channel_id}_{date.strftime('%Y%m%d')}.html"
                filepath = self.output_dir / filename
                filepath.write_text(html_content)
                
                logger.info(f"Channel detail report generated: {filepath}")
                return str(filepath)
                
        except Exception as e:
            logger.error(f"Error generating channel detail report: {e}")
            return ""
    
    def generate_comprehensive_html_report(self, date: Optional[datetime] = None) -> Dict[str, str]:
        """
        Generate all HTML reports for a given date
        
        Args:
            date: Date for the report (defaults to today)
            
        Returns:
            Dictionary with report file paths
        """
        if date is None:
            date = datetime.utcnow()
        
        reports = {}
        
        try:
            # Generate dashboard report
            dashboard_report = self.generate_dashboard_report(date)
            if dashboard_report:
                reports['dashboard'] = dashboard_report
            
            # Generate channel detail reports for all channels
            with get_db_session() as session:
                channels = session.query(Channel).all()
                for channel in channels:
                    channel_report = self.generate_channel_detail_report(channel.channel_id, date)
                    if channel_report:
                        reports[f'channel_{channel.channel_id}'] = channel_report
            
            logger.info(f"Comprehensive HTML report generated with {len(reports)} files")
            return reports
            
        except Exception as e:
            logger.error(f"Error generating comprehensive HTML report: {e}")
            return reports 