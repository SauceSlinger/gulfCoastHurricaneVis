#!/usr/bin/env python3
"""
Simple Loading Launcher for Hurricane Dashboard
Clean loading interface that hands off to the main dashboard
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher with integrated loading messages"""
    
    print("🌀 Hurricane Dashboard - Loading")
    print("=" * 40)
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    try:
        # Show loading steps
        print("🐍 Checking Python version...")
        if sys.version_info < (3, 8):
            print(f"❌ Python 3.8+ required, found {sys.version.split()[0]}")
            return False
        print(f"✅ Python {sys.version.split()[0]} detected")
        
        print("\n📦 Verifying dependencies...")
        dependencies = ['customtkinter', 'matplotlib', 'pandas', 'numpy', 'psutil']
        missing_deps = []
        
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"  ✓ {dep}")
            except ImportError:
                missing_deps.append(dep)
                print(f"  ✗ {dep} - MISSING")
        
        if missing_deps:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            print("📦 Install with: pip install " + " ".join(missing_deps))
            return False
        print("✅ All dependencies verified")
        
        print("\n📁 Validating required files...")
        required_files = [
            'tabbed_native_dashboard.py',
            'native_visualizations.py', 
            'settings_manager.py',
            'aesthetic_theme.py'
        ]
        
        missing_files = []
        for file in required_files:
            if Path(file).exists():
                print(f"  ✓ {file}")
            else:
                missing_files.append(file)
                print(f"  ✗ {file} - MISSING")
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        print("✅ All required files present")
        
        print("\n📊 Checking data files...")
        if Path('storms.csv').exists():
            print("  ✓ Found storms.csv")
            print("✅ Data files ready")
        else:
            print("  ! storms.csv not found (can be loaded manually)")
            print("⚠️ No data files found (manual loading required)")
        
        print("\n🎨 Testing matplotlib backend...")
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            print("  ✓ Matplotlib TkAgg backend loaded")
            
            import tkinter as tk
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            
            # Quick test
            root = tk.Tk()
            root.withdraw()
            
            fig = Figure(figsize=(2, 2))
            ax = fig.add_subplot(111)
            ax.plot([1, 2], [1, 2])
            
            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas.draw()
            root.destroy()
            
            print("  ✓ Backend compatibility verified")
            print("✅ Matplotlib backend ready")
        except Exception as e:
            print(f"  ✗ Backend test failed: {str(e)}")
            print(f"❌ Matplotlib backend error")
            return False
        
        print("\n🔧 Launching Hurricane Dashboard...")
        print("🎯 Enhanced Features:")
        print("   • 📊 Overview tab with comprehensive data summary")
        print("   • 📈 Full-screen timeline visualizations")
        print("   • 🗺️ Dedicated map visualization tab")
        print("   • 📋 Statistical analysis with multi-panel layout")
        print("   • ⚙️ Integrated settings management")
        print("   • 🔄 Smart refresh system with data reloading")
        print("   • 💾 Export capabilities and performance monitoring")
        print("")
        
        # Import and launch dashboard
        from tabbed_native_dashboard import TabbedNativeDashboard
        
        print("✨ Initializing dashboard components...")
        dashboard = TabbedNativeDashboard()
        
        print("🚀 Starting Hurricane Dashboard...")
        dashboard.run()
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Launch interrupted by user")
        return True
        
    except Exception as e:
        print(f"\n❌ Launch failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure all dependencies are installed:")
        print("      pip install customtkinter matplotlib pandas numpy psutil")
        print("   2. Verify all Python files are in the current directory")
        print("   3. Check system GUI support: python -c 'import tkinter; tkinter.Tk()'")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Hurricane Dashboard session completed successfully")
        sys.exit(0)
    else:
        sys.exit(1)