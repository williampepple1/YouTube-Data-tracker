"""
Database connection and session management for YouTube Data Tracker
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from ..config import config
from .models import Base

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    config.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_tables() -> None:
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_session() as session:
            # Use session for database operations
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Usage in FastAPI endpoints:
        def get_channel_stats(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    with get_db_session() as session:
        yield session


def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_db_session() as session:
            session.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def initialize_database() -> None:
    """Initialize database with tables and test connection"""
    logger.info("Initializing database...")
    
    # Test connection first
    if not test_connection():
        raise ConnectionError("Cannot connect to database")
    
    # Create tables
    create_tables()
    
    logger.info("Database initialization completed successfully") 