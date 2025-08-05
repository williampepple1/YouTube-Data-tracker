#!/usr/bin/env python3
"""
Script to run the YouTube Data Tracker FastAPI server
"""
import sys
import os
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api import app
from src.config import config
from src.database import initialize_database

def main():
    """Run the FastAPI server"""
    print("YouTube Data Tracker - API Server")
    print("=" * 50)
    
    try:
        # Initialize database
        print("🔧 Initializing database...")
        initialize_database()
        print("✅ Database initialized successfully")
        
        # Start server
        print("🚀 Starting FastAPI server...")
        print(f"📖 API Documentation: http://localhost:8000/docs")
        print(f"📚 ReDoc Documentation: http://localhost:8000/redoc")
        print(f"🏥 Health Check: http://localhost:8000/health")
        print("=" * 50)
        
        uvicorn.run(
            "src.api.endpoints:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level=config.LOG_LEVEL.lower()
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 