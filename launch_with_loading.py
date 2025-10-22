#!/usr/bin/env python3
"""
Hurricane Dashboard Launcher with Professional Loading Screen
Enhanced launcher with beautiful loading interface and progress tracking
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher function with loading screen"""
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    try:
        # Import and launch with loading screen
        from loading_window import launch_with_loading_screen
        
        print("🌀 Hurricane Dashboard - Professional Edition")
        print("🚀 Starting with enhanced loading interface...")
        print()
        
        # Launch with professional loading screen
        launch_with_loading_screen()
        
    except ImportError as e:
        # Fallback to original launcher if loading window fails
        print(f"⚠️ Loading screen unavailable: {e}")
        print("🔄 Falling back to standard launcher...")
        
        try:
            from launch_tabbed import main as original_main
            return original_main()
        except Exception as fallback_error:
            print(f"❌ Fallback launcher failed: {fallback_error}")
            return False
            
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