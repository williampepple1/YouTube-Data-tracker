#!/usr/bin/env python3
"""
Test script to verify database setup
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import config
from src.database import initialize_database, get_db_session, Channel, DailyStats
from datetime import datetime

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    print(f"Database URL: {config.DATABASE_URL}")
    print(f"Report output dir: {config.REPORT_OUTPUT_DIR}")
    print(f"Template dir: {config.TEMPLATE_DIR}")
    print("Configuration test passed!")

def test_database():
    """Test database connection and models"""
    print("\nTesting database...")
    
    try:
        # Initialize database
        initialize_database()
        print("Database initialization successful!")
        
        # Test session creation
        with get_db_session() as session:
            # Test basic query
            result = session.execute("SELECT 1 as test").fetchone()
            print(f"Database query test: {result}")
            
            # Test model creation (without committing)
            test_channel = Channel(
                channel_id="UC_test",
                title="Test Channel",
                description="Test channel for database testing"
            )
            session.add(test_channel)
            print("Model creation test passed!")
            
    except Exception as e:
        print(f"Database test failed: {e}")
        return False
    
    print("Database test passed!")
    return True

if __name__ == "__main__":
    print("YouTube Data Tracker - Database Setup Test")
    print("=" * 50)
    
    test_config()
    success = test_database()
    
    if success:
        print("\n✅ All tests passed! Database setup is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1) 