"""
Test the embedded visualization functionality
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from data_processor import HurricaneDataProcessor
from visualizations import HurricaneVisualizations
import tempfile
import os

def test_embedded_viz():
    """Test that we can generate static images from Plotly"""
    print("=== Testing Embedded Visualization Functionality ===")
    
    try:
        # Initialize components
        processor = HurricaneDataProcessor()
        visualizer = HurricaneVisualizations()
        
        if processor.gulf_coast_data is None:
            print("❌ No data available")
            return False
        
        # Test timeline image generation
        annual_data = processor.get_annual_storm_summary()
        timeline_fig = visualizer.create_timeline_overview(annual_data)
        
        # Test saving as image
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, "test_timeline.png")
        
        # This is the key test - can we export Plotly to PNG?
        timeline_fig.write_image(img_path, width=800, height=500)
        
        # Check if file was created and has reasonable size
        if os.path.exists(img_path) and os.path.getsize(img_path) > 10000:  # >10KB
            print("✅ Timeline image generation successful")
            file_size = os.path.getsize(img_path) / 1024
            print(f"   Image size: {file_size:.1f} KB")
        else:
            print("❌ Timeline image generation failed")
            return False
        
        # Test map image generation
        storm_tracks = processor.get_storm_tracks(limit=3)
        map_fig = visualizer.create_storm_track_map(storm_tracks)
        
        img_path_map = os.path.join(temp_dir, "test_map.png")
        map_fig.write_image(img_path_map, width=800, height=500)
        
        if os.path.exists(img_path_map) and os.path.getsize(img_path_map) > 10000:
            print("✅ Map image generation successful")
            file_size = os.path.getsize(img_path_map) / 1024
            print(f"   Image size: {file_size:.1f} KB")
        else:
            print("❌ Map image generation failed")
            return False
        
        # Test PIL image loading
        try:
            from PIL import Image, ImageTk
            
            # Test loading the timeline image
            img = Image.open(img_path)
            resized_img = img.resize((400, 300), Image.Resampling.LANCZOS)
            print(f"✅ PIL image processing successful")
            print(f"   Original size: {img.size}, Resized: {resized_img.size}")
            
        except ImportError:
            print("❌ PIL not available - image display will use fallback")
            return False
        except Exception as e:
            print(f"❌ PIL processing error: {e}")
            return False
        
        # Clean up
        os.remove(img_path)
        os.remove(img_path_map)
        os.rmdir(temp_dir)
        
        print("\n🎉 All embedded visualization tests passed!")
        print("📊 Dashboard can now display charts directly inside the interface!")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedded visualization test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_embedded_viz()
    
    if success:
        print("\n" + "="*60)
        print("✅ ENHANCED DASHBOARD READY!")
        print("🎯 New Features Available:")
        print("   • Embedded visualizations inside the dashboard")
        print("   • Static image display of Plotly charts")
        print("   • Dual mode: Embedded view + Browser view")
        print("   • Automatic chart summaries and statistics")
        print("\n🚀 Run: python dashboard.py")
    else:
        print("\n❌ Setup issues detected - check dependencies")