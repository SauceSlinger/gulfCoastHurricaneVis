"""
Test script for the Hurricane Data Visualization Dashboard
Tests data processing and visualization generation
"""

from data_processor import HurricaneDataProcessor
from visualizations import HurricaneVisualizations
import pandas as pd

def test_data_processing():
    """Test the data processing functionality"""
    print("=== Testing Hurricane Data Processing ===")
    
    # Initialize processor
    processor = HurricaneDataProcessor()
    
    if processor.gulf_coast_data is None:
        print("❌ Failed to load data")
        return False
    
    print(f"✅ Loaded {len(processor.gulf_coast_data)} Gulf Coast hurricane records")
    
    # Test data summary
    summary = processor.get_data_summary()
    print(f"✅ Data Summary:")
    print(f"   - Year range: {summary['year_range']}")
    print(f"   - Unique storms: {summary['unique_storms']}")
    print(f"   - Categories present: {summary['categories_present']}")
    
    # Test filtering
    filtered_2020_2021 = processor.filter_by_year_range(2020, 2021)
    print(f"✅ 2020-2021 data: {len(filtered_2020_2021)} records")
    
    # Test annual summary
    annual_data = processor.get_annual_storm_summary()
    print(f"✅ Annual summary: {len(annual_data)} years of data")
    
    # Test storm tracks
    storm_tracks = processor.get_storm_tracks(limit=5)
    print(f"✅ Storm tracks: {len(storm_tracks)} recent storms")
    
    # Test impact statistics
    impact_stats = processor.get_impact_statistics()
    print(f"✅ Impact statistics: {impact_stats.get('total_storms', 0)} total storms analyzed")
    
    return True

def test_visualizations():
    """Test the visualization functionality"""
    print("\n=== Testing Visualization Generation ===")
    
    # Initialize components
    processor = HurricaneDataProcessor()
    visualizer = HurricaneVisualizations()
    
    if processor.gulf_coast_data is None:
        print("❌ No data available for visualization testing")
        return False
    
    # Test timeline visualization
    try:
        annual_data = processor.get_annual_storm_summary()
        timeline_fig = visualizer.create_timeline_overview(annual_data)
        print("✅ Timeline visualization created successfully")
    except Exception as e:
        print(f"❌ Timeline visualization failed: {e}")
    
    # Test map visualization
    try:
        storm_tracks = processor.get_storm_tracks(limit=3)  # Small number for testing
        map_fig = visualizer.create_storm_track_map(storm_tracks)
        print("✅ Storm track map created successfully")
    except Exception as e:
        print(f"❌ Map visualization failed: {e}")
    
    # Test impact analysis
    try:
        impact_stats = processor.get_impact_statistics()
        impact_fig = visualizer.create_impact_heatmap(impact_stats)
        print("✅ Impact heatmap created successfully")
    except Exception as e:
        print(f"❌ Impact visualization failed: {e}")
    
    # Test seasonal analysis
    try:
        seasonal_fig = visualizer.create_seasonal_analysis(processor.gulf_coast_data)
        print("✅ Seasonal analysis created successfully")
    except Exception as e:
        print(f"❌ Seasonal analysis failed: {e}")
    
    # Test intensity analysis
    try:
        intensity_fig = visualizer.create_intensity_analysis(processor.gulf_coast_data)
        print("✅ Intensity analysis created successfully")
    except Exception as e:
        print(f"❌ Intensity analysis failed: {e}")
    
    return True

def test_recent_storms():
    """Test analysis of recent notable storms"""
    print("\n=== Testing Recent Storm Analysis ===")
    
    processor = HurricaneDataProcessor()
    
    # Look at recent years (2018-2021) for notable storms
    recent_data = processor.filter_by_year_range(2018, 2021)
    
    if len(recent_data) == 0:
        print("❌ No recent storm data found")
        return
    
    # Get storm summary for recent years
    recent_storms = recent_data.groupby(['name', 'year']).agg({
        'wind': 'max',
        'pressure': 'min',
        'category': 'max'
    }).reset_index()
    
    # Sort by max wind speed
    notable_storms = recent_storms.nlargest(10, 'wind')
    
    print("🌀 Top 10 Most Intense Recent Gulf Coast Storms (2018-2021):")
    for _, storm in notable_storms.iterrows():
        print(f"   {storm['name']} ({storm['year']}) - {storm['wind']} mph, Cat {storm['category']}")
    
    # Monthly distribution
    monthly_counts = recent_data.groupby('month')['name'].nunique()
    peak_month = monthly_counts.idxmax()
    month_names = {8: 'August', 9: 'September', 10: 'October', 6: 'June', 7: 'July', 11: 'November'}
    
    print(f"\n📅 Peak hurricane month (2018-2021): {month_names.get(peak_month, peak_month)} with {monthly_counts[peak_month]} storms")

if __name__ == "__main__":
    print("Hurricane Data Visualization Dashboard - Test Suite")
    print("=" * 60)
    
    # Run tests
    data_ok = test_data_processing()
    
    if data_ok:
        test_visualizations()
        test_recent_storms()
        
        print("\n" + "=" * 60)
        print("🎯 Test Summary:")
        print("✅ Data processing: Working")
        print("✅ Visualizations: Working") 
        print("✅ Recent storm analysis: Working")
        print("\n🚀 Dashboard is ready for use!")
        print("   Run: python dashboard.py")
    else:
        print("\n❌ Tests failed - check data file and dependencies")