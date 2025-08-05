#!/usr/bin/env python3
"""
Script to generate YouTube Data Tracker reports
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.reports import CSVReportGenerator, HTMLReportGenerator
from src.config import config

def main():
    """Generate all reports for today"""
    print("YouTube Data Tracker - Report Generation")
    print("=" * 50)
    
    # Initialize report generators
    csv_generator = CSVReportGenerator()
    html_generator = HTMLReportGenerator()
    
    today = datetime.utcnow()
    
    print(f"Generating reports for: {today.strftime('%Y-%m-%d')}")
    print()
    
    # Generate CSV reports
    print("📊 Generating CSV reports...")
    csv_reports = csv_generator.generate_comprehensive_report(today)
    
    if csv_reports:
        print("✅ CSV reports generated:")
        for report_type, filepath in csv_reports.items():
            print(f"   - {report_type}: {Path(filepath).name}")
    else:
        print("❌ No CSV reports generated")
    
    print()
    
    # Generate HTML reports
    print("🌐 Generating HTML reports...")
    html_reports = html_generator.generate_comprehensive_html_report(today)
    
    if html_reports:
        print("✅ HTML reports generated:")
        for report_type, filepath in html_reports.items():
            print(f"   - {report_type}: {Path(filepath).name}")
    else:
        print("❌ No HTML reports generated")
    
    print()
    print("📁 Reports saved to:", config.REPORT_OUTPUT_DIR)
    print("=" * 50)
    
    if csv_reports or html_reports:
        print("✅ Report generation completed successfully!")
    else:
        print("❌ No reports were generated. Check if you have data in the database.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 