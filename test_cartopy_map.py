#!/usr/bin/env python3
"""
Simple test script to verify Cartopy geographical background implementation
"""

import sys
import os
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for GUI support
import matplotlib.pyplot as plt
from native_visualizations import NativeVisualizationEngine

def test_cartopy_map():
    """Test the Cartopy map visualization with geographical background"""
    print("🗺️  Testing Cartopy geographical background implementation...")

    # Load storm data
    try:
        data = pd.read_csv('storms.csv')
        print(f"✅ Loaded {len(data):,} storm records from storms.csv")
    except Exception as e:
        print(f"❌ Failed to load storm data: {e}")
        return False

    # Initialize visualization engine
    try:
        engine = NativeVisualizationEngine()
        print("✅ Native visualization engine initialized")
    except Exception as e:
        print(f"❌ Failed to initialize visualization engine: {e}")
        return False

    # Create a simple test window to display the map
    try:
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Create root window
        root = tk.Tk()
        root.title("Cartopy Map Test - Gulf Coast Hurricanes")
        root.geometry("1200x800")

        # Create frame for the map
        map_frame = tk.Frame(root)
        map_frame.pack(fill=tk.BOTH, expand=True)

        # Generate map visualization
        print("🎨 Generating Cartopy map visualization...")
        result = engine.generate_map_visualization(data, map_frame, [])

        if result and 'figure' in result:
            print("✅ Map visualization generated successfully")
            print("🗺️  Geographical background should show:")
            print("   • White coastline outlines")
            print("   • Light gray landmasses")
            print("   • Light blue ocean background")
            print("   • Storm tracks in various colors by intensity")
            print("   • Proper zorder layering (geography behind storms)")

            # Keep window open for inspection
            print("\n🔍 Inspect the map window that opened.")
            print("   Look for:")
            print("   • White outline geographical features")
            print("   • Storm tracks appearing above the geography")
            print("   • Proper latitude/longitude coordinates")
            print("   • Gulf Coast and Caribbean regions visible")
            print("\n❌ Close the window when done inspecting")

            root.mainloop()
            return True
        else:
            print("❌ Map visualization generation failed")
            return False

    except Exception as e:
        print(f"❌ Failed to create test window: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🌀 Cartopy Geographical Background Test")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False

    print(f"✅ Python {sys.version.split()[0]} detected")

    # Check required modules
    required_modules = ['pandas', 'matplotlib', 'cartopy', 'numpy']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} missing")

    if missing_modules:
        print(f"\n📦 Install missing modules: pip install {' '.join(missing_modules)}")
        return False

    # Run the test
    success = test_cartopy_map()

    if success:
        print("\n🎉 Cartopy geographical background test completed successfully!")
        print("   The white outline map should now appear behind storm tracks.")
    else:
        print("\n❌ Cartopy geographical background test failed.")
        print("   Check the error messages above for troubleshooting.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)