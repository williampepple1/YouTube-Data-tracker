# YouTube Data Tracker

A comprehensive tool to track YouTube channel statistics and generate daily reports.

## Features

- Fetch daily stats (views, likes, comments) for a list of channels
- Store historical data in PostgreSQL
- Generate daily CSV + HTML reports
- Schedule the pipeline using Airflow or cron
- FastAPI endpoint to query data

## Project Structure

```
youtube-data-tracker/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py      # SQLAlchemy models
│   │   └── connection.py  # Database connection
│   ├── youtube/
│   │   ├── __init__.py
│   │   └── api.py         # YouTube API client
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── csv_generator.py
│   │   └── html_generator.py
│   └── api/
│       ├── __init__.py
│       └── endpoints.py   # FastAPI endpoints
├── dags/                  # Airflow DAGs
├── templates/             # HTML report templates
├── data/                  # Generated reports
├── tests/                 # Test files
├── requirements.txt
└── .env.example
```

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure your settings
4. Set up PostgreSQL database
5. Configure YouTube API credentials

## Environment Variables

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql://user:password@localhost/youtube_tracker
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
```

## Usage

- Run the FastAPI server: `uvicorn src.api.endpoints:app --reload`
- Run Airflow scheduler: `airflow scheduler`
- Generate reports manually: `python -m src.reports.csv_generator`

## Development

- Run tests: `pytest`
- Format code: `black src/`
- Lint code: `flake8 src/` 