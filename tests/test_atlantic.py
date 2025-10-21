"""
Test the full Atlantic Basin visualization functionality
"""

from data_processor import HurricaneDataProcessor
from visualizations import HurricaneVisualizations
import tempfile
import os

def test_full_atlantic_view():
    """Test that we can generate full Atlantic Basin visualizations"""
    print("=== Testing Full Atlantic Basin Functionality ===")
    
    try:
        # Initialize components
        processor = HurricaneDataProcessor()
        visualizer = HurricaneVisualizations()
        
        if processor.full_atlantic_data is None:
            print("❌ No full Atlantic data available")
            return False
        
        print(f"✅ Full Atlantic dataset loaded: {len(processor.full_atlantic_data):,} records")
        print(f"✅ Total Atlantic storms: {processor.full_atlantic_data.groupby(['name', 'year']).size().count()}")
        
        # Test full Atlantic storm tracks
        atlantic_tracks = processor.get_storm_tracks(processor.full_atlantic_data, limit=10)
        print(f"✅ Atlantic storm tracks generated: {len(atlantic_tracks)} storms")
        
        # Test Atlantic map visualization
        atlantic_map = visualizer.create_storm_track_map(
            atlantic_tracks, 
            title="Full Atlantic Basin Hurricane Tracks",
            map_scope="atlantic"
        )
        
        # Test saving Atlantic map
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, "atlantic_map.png")
        atlantic_map.write_image(img_path, width=800, height=500)
        
        if os.path.exists(img_path) and os.path.getsize(img_path) > 10000:
            print("✅ Full Atlantic map generation successful")
            file_size = os.path.getsize(img_path) / 1024
            print(f"   Image size: {file_size:.1f} KB")
        else:
            print("❌ Atlantic map generation failed")
            return False
        
        # Test geographic scope comparison
        gulf_tracks = processor.get_storm_tracks(processor.gulf_coast_data, limit=5)
        
        print("\n📊 Geographic Scope Comparison:")
        
        # Atlantic basin statistics
        atlantic_lats = []
        atlantic_lons = []
        for track in atlantic_tracks.values():
            atlantic_lats.extend([lat for lat in track['lats'] if lat is not None])
            atlantic_lons.extend([lon for lon in track['lons'] if lon is not None])
        
        if atlantic_lats and atlantic_lons:
            print(f"🌊 Atlantic Basin Coverage:")
            print(f"   Latitude: {min(atlantic_lats):.1f}° to {max(atlantic_lats):.1f}°N")
            print(f"   Longitude: {min(atlantic_lons):.1f}° to {max(atlantic_lons):.1f}°W")
            print(f"   Lat span: {max(atlantic_lats) - min(atlantic_lats):.1f}°")
            print(f"   Lon span: {max(atlantic_lons) - min(atlantic_lons):.1f}°")
        
        # Gulf Coast statistics  
        gulf_lats = []
        gulf_lons = []
        for track in gulf_tracks.values():
            gulf_lats.extend([lat for lat in track['lats'] if lat is not None])
            gulf_lons.extend([lon for lon in track['lons'] if lon is not None])
        
        if gulf_lats and gulf_lons:
            print(f"🏖️ Gulf Coast Focus:")
            print(f"   Latitude: {min(gulf_lats):.1f}° to {max(gulf_lats):.1f}°N")
            print(f"   Longitude: {min(gulf_lons):.1f}° to {max(gulf_lons):.1f}°W")
            print(f"   Lat span: {max(gulf_lats) - min(gulf_lats):.1f}°")
            print(f"   Lon span: {max(gulf_lons) - min(gulf_lons):.1f}°")
        
        # Notable storms by intensity across full basin
        all_atlantic_data = processor.full_atlantic_data
        recent_atlantic = all_atlantic_data[all_atlantic_data['year'] >= 2018]
        
        if len(recent_atlantic) > 0:
            top_storms = recent_atlantic.groupby(['name', 'year']).agg({
                'wind': 'max',
                'category': 'max'
            }).reset_index().nlargest(10, 'wind')
            
            print(f"\n🌀 Top Atlantic Storms (2018-2021):")
            for _, storm in top_storms.iterrows():
                print(f"   {storm['name']} ({storm['year']}) - {storm['wind']} mph, Cat {storm['category']}")
        
        # Clean up
        os.remove(img_path)
        os.rmdir(temp_dir)
        
        print("\n🎉 Full Atlantic Basin visualization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Full Atlantic test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_full_atlantic_view()
    
    if success:
        print("\n" + "="*60)
        print("✅ ENHANCED GEOGRAPHIC SCOPE READY!")
        print("🌍 New Features Available:")
        print("   • Full Atlantic Basin coverage (639 storms)")
        print("   • Geographic scope selector in dashboard")
        print("   • Comprehensive hurricane tracking from Africa to Americas")
        print("   • Enhanced map visualizations with landmarks")
        print("   • Cohesive statistics across both scopes")
        print("\n🚀 Run: python dashboard.py")
        print("   Select 'Full Atlantic Basin' for comprehensive view")
    else:
        print("\n❌ Setup issues detected - check dependencies")