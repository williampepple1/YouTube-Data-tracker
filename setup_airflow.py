#!/usr/bin/env python3
"""
Setup script for Airflow configuration
"""
import sys
import os
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import config

def setup_airflow():
    """Set up Airflow for the YouTube Data Tracker project"""
    print("YouTube Data Tracker - Airflow Setup")
    print("=" * 50)
    
    try:
        # Set Airflow environment variables
        os.environ['AIRFLOW_HOME'] = str(config.AIRFLOW_HOME)
        os.environ['AIRFLOW__CORE__SQL_ALCHEMY_CONN'] = config.AIRFLOW_SQL_ALCHEMY_CONN
        os.environ['AIRFLOW__CORE__EXECUTOR'] = config.AIRFLOW_EXECUTOR
        
        # Create Airflow home directory
        config.AIRFLOW_HOME.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created Airflow home directory: {config.AIRFLOW_HOME}")
        
        # Initialize Airflow database
        print("🔧 Initializing Airflow database...")
        result = subprocess.run(
            ['airflow', 'db', 'init'],
            capture_output=True,
            text=True,
            env=os.environ
        )
        
        if result.returncode == 0:
            print("✅ Airflow database initialized successfully")
        else:
            print(f"❌ Error initializing Airflow database: {result.stderr}")
            return False
        
        # Create Airflow user
        print("👤 Creating Airflow user...")
        result = subprocess.run([
            'airflow', 'users', 'create',
            '--username', 'admin',
            '--firstname', 'Admin',
            '--lastname', 'User',
            '--role', 'Admin',
            '--email', 'admin@youtube-tracker.com',
            '--password', 'admin123'
        ], capture_output=True, text=True, env=os.environ)
        
        if result.returncode == 0:
            print("✅ Airflow user created successfully")
        else:
            print(f"⚠️  Warning: Could not create Airflow user: {result.stderr}")
        
        # Set DAGs folder
        dags_folder = Path(__file__).parent / 'dags'
        os.environ['AIRFLOW__CORE__DAGS_FOLDER'] = str(dags_folder)
        
        print(f"📁 DAGs folder set to: {dags_folder}")
        
        # Test Airflow installation
        print("🧪 Testing Airflow installation...")
        result = subprocess.run(
            ['airflow', 'version'],
            capture_output=True,
            text=True,
            env=os.environ
        )
        
        if result.returncode == 0:
            print(f"✅ Airflow version: {result.stdout.strip()}")
        else:
            print(f"❌ Error testing Airflow: {result.stderr}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Airflow setup completed successfully!")
        print("\nNext steps:")
        print("1. Start Airflow webserver: airflow webserver --port 8080")
        print("2. Start Airflow scheduler: airflow scheduler")
        print("3. Access Airflow UI: http://localhost:8080")
        print("4. Login with: admin / admin123")
        print("\nDAGs available:")
        print("- youtube_data_collection: Daily data collection")
        print("- channel_processing: Individual channel processing")
        print("- weekly_reports: Weekly report generation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Airflow setup: {e}")
        return False

def start_airflow_services():
    """Start Airflow webserver and scheduler"""
    print("🚀 Starting Airflow services...")
    
    try:
        # Set environment variables
        os.environ['AIRFLOW_HOME'] = str(config.AIRFLOW_HOME)
        os.environ['AIRFLOW__CORE__SQL_ALCHEMY_CONN'] = config.AIRFLOW_SQL_ALCHEMY_CONN
        os.environ['AIRFLOW__CORE__EXECUTOR'] = config.AIRFLOW_EXECUTOR
        os.environ['AIRFLOW__CORE__DAGS_FOLDER'] = str(Path(__file__).parent / 'dags')
        
        print("📊 Starting Airflow webserver...")
        webserver_process = subprocess.Popen(
            ['airflow', 'webserver', '--port', '8080'],
            env=os.environ
        )
        
        print("⏰ Starting Airflow scheduler...")
        scheduler_process = subprocess.Popen(
            ['airflow', 'scheduler'],
            env=os.environ
        )
        
        print("✅ Airflow services started successfully!")
        print("🌐 Access Airflow UI: http://localhost:8080")
        print("👤 Login: admin / admin123")
        print("\nPress Ctrl+C to stop services...")
        
        try:
            webserver_process.wait()
            scheduler_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping Airflow services...")
            webserver_process.terminate()
            scheduler_process.terminate()
            print("✅ Airflow services stopped")
        
    except Exception as e:
        print(f"❌ Error starting Airflow services: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        start_airflow_services()
    else:
        success = setup_airflow()
        if success:
            print("\nWould you like to start Airflow services now? (y/n): ", end="")
            response = input().lower().strip()
            if response in ['y', 'yes']:
                start_airflow_services()
        else:
            sys.exit(1) 