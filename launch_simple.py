#!/usr/bin/env python3
"""
Quick Hurricane Dashboard Launcher (CSV Mode)
Launch the dashboard directly using CSV data without database setup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_basic_requirements():
    """Check if basic required packages are installed"""
    required_packages = [
        'customtkinter',
        'plotly',
        'pandas',
        'numpy'
    ]
    
    print("🔍 Checking basic requirements...")
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
    
    return True

def check_data_file():
    """Check if the storms.csv data file exists"""
    csv_file = Path("storms.csv")
    if csv_file.exists():
        print(f"✅ Data file found: storms.csv ({csv_file.stat().st_size // 1024} KB)")
        return True
    else:
        print("❌ Data file not found: storms.csv")
        print("💡 Please ensure storms.csv is in the current directory")
        return False

def launch_dashboard():
    """Launch the main dashboard application"""
    print("\n🚀 Launching Hurricane Dashboard (CSV Mode)...")
    
    try:
        # Launch the dashboard
        os.execv(sys.executable, [sys.executable, 'dashboard.py'])
        
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")
        return False

def main():
    """Main launcher function for CSV mode"""
    print("🌀 Gulf Coast Hurricane Visualization Dashboard")
    print("=" * 55)
    print("Quick Launch - CSV Mode")
    print("=" * 55)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Check basic requirements
    if not check_basic_requirements():
        print("\n❌ Requirements check failed. Please install missing packages manually.")
        print("💡 Try: pip install customtkinter plotly pandas numpy")
        sys.exit(1)
    
    # Step 2: Check data file
    if not check_data_file():
        print("\n❌ Data file check failed.")
        print("💡 Make sure storms.csv is in the project directory")
        sys.exit(1)
    
    # Step 3: Launch dashboard
    print("\n🎯 Everything looks good! Launching dashboard...")
    print("ℹ️  Running in CSV mode (no database required)")
    print("💡 For enhanced performance, use launch_dashboard.py with PostgreSQL setup")
    
    launch_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Launch cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)