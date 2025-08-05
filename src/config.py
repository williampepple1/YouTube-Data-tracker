"""
Configuration management for YouTube Data Tracker
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class"""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/youtube_tracker")
    
    # YouTube API Configuration
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    YOUTUBE_CLIENT_ID: Optional[str] = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET: Optional[str] = os.getenv("YOUTUBE_CLIENT_SECRET")
    
    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    REPORT_OUTPUT_DIR: Path = Path(os.getenv("REPORT_OUTPUT_DIR", "./data/reports"))
    TEMPLATE_DIR: Path = Path(os.getenv("TEMPLATE_DIR", "./templates"))
    
    # Airflow Settings
    AIRFLOW_HOME: Path = Path(os.getenv("AIRFLOW_HOME", "./airflow"))
    AIRFLOW_SQL_ALCHEMY_CONN: str = os.getenv(
        "AIRFLOW__CORE__SQL_ALCHEMY_CONN", 
        "postgresql://user:password@localhost/airflow"
    )
    AIRFLOW_EXECUTOR: str = os.getenv("AIRFLOW__CORE__EXECUTOR", "LocalExecutor")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values"""
        required_vars = [
            ("YOUTUBE_API_KEY", cls.YOUTUBE_API_KEY),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist"""
        cls.REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        cls.AIRFLOW_HOME.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config() 