#!/usr/bin/env python3
"""
Tabbed Dashboard Launcher
Launch the hurricane dashboard with tabbed interface for maximum visualization space
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    try:
        import matplotlib
        matplotlib.use('TkAgg')
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except ImportError:
        missing_deps.append("matplotlib")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n📦 Install missing dependencies with:")
        print(f"   pip install {' '.join(missing_deps)}")
        return False
    
    return True

def validate_files():
    """Check if all required files exist"""
    required_files = [
        'tabbed_native_dashboard.py',
        'native_visualizations.py',
        'settings_manager.py',
        'data_processor_db.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    return True

def check_data_files():
    """Check for data files"""
    data_files = ['storms.csv']
    
    available_data = []
    for file in data_files:
        if Path(file).exists():
            available_data.append(file)
    
    if not available_data:
        print("⚠️  No data files found. You'll need to load data manually.")
        print("   Expected data files: storms.csv")
    else:
        print(f"✅ Found data files: {', '.join(available_data)}")
    
    return True

def test_matplotlib_backend():
    """Test if matplotlib TkAgg backend works"""
    try:
        import matplotlib
        matplotlib.use('TkAgg')
        
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        
        # Test creating a simple plot
        root = tk.Tk()
        root.withdraw()  # Hide the test window
        
        fig = Figure(figsize=(8, 6))  # Larger test size for tabbed interface
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3], [1, 2, 3])
        
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()
        
        # Clean up
        root.destroy()
        
        print("✅ Matplotlib TkAgg backend working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Matplotlib TkAgg backend test failed: {e}")
        print("   This may cause visualization issues")
        return False

def main():
    """Main launcher function"""
    print("🚀 Tabbed Hurricane Dashboard Launcher")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check dependencies
    print("\n🔍 Checking dependencies...")
    if not check_dependencies():
        return False
    print("✅ All dependencies available")
    
    # Validate files
    print("\n📁 Validating required files...")
    if not validate_files():
        return False
    print("✅ All required files present")
    
    # Check data files
    print("\n📊 Checking for data files...")
    check_data_files()
    
    # Test matplotlib backend
    print("\n🎨 Testing matplotlib backend...")
    test_matplotlib_backend()
    
    # Launch dashboard
    print("\n🌀 Launching Tabbed Hurricane Dashboard...")
    print("   Enhanced Features:")
    print("   • 📊 Overview tab with comprehensive data summary")
    print("   • 📈 Full-screen timeline visualizations")
    print("   • 🗺️  Dedicated map visualization tab")
    print("   • 📋 Statistical analysis with multi-panel layout")
    print("   • ⚙️  Integrated settings management per visualization")
    print("   • 🔄 Smart refresh system with data reloading")
    print("   • 💾 Export capabilities and performance monitoring")
    print("   • 🎯 Maximum screen space for each visualization type")
    
    try:
        from tabbed_native_dashboard import TabbedNativeDashboard
        
        # Create and run tabbed dashboard
        dashboard = TabbedNativeDashboard()
        dashboard.run()
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to launch tabbed dashboard: {e}")
        import traceback
        print("\nFull error details:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure all dependencies are installed:")
        print("      pip install customtkinter matplotlib pandas numpy psutil")
        print("   2. Check that all Python files are in the current directory")
        print("   3. Verify that your system supports GUI applications")
        print("   4. Try running: python -c 'import tkinter; tkinter.Tk()'")
        print("   5. For large visualizations, ensure sufficient system memory")
        sys.exit(1)
    else:
        print("\n✅ Tabbed dashboard session completed successfully")
        sys.exit(0)