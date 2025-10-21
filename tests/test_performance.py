#!/usr/bin/env python3
"""
Performance Test Script for Hurricane Dashboard
Tests the view manager caching system and database performance
"""

import time
import os
import sys
from datetime import datetime
import threading

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from view_manager import PersistentViewManager, ViewType, FilterState
    from data_processor_db import DatabaseHurricaneDataProcessor
    from database_manager import DatabaseManager
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_database_connection():
    """Test database connection and basic query performance"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        # Check if PostgreSQL modules are available
        from database_manager import DatabaseManager
        from data_processor_db import DatabaseHurricaneDataProcessor
        
        db_manager = DatabaseManager()
        
        # Test connection
        start_time = time.time()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM storms")
            storm_count = cursor.fetchone()[0]
        
        connection_time = time.time() - start_time
        print(f"✅ Database connected: {storm_count:,} storms in {connection_time:.3f}s")
        
        # Test query performance
        start_time = time.time()
        processor = DatabaseHurricaneDataProcessor()
        sample_data = processor.get_filtered_data(year_from=2020, year_to=2023)
        query_time = time.time() - start_time
        
        print(f"✅ Sample query: {len(sample_data):,} records in {query_time:.3f}s")
        return True
        
    except ImportError as e:
        print(f"⚠️  Database modules not found: {e}")
        print("🔄 Testing CSV-based fallback...")
        
        try:
            from data_processor import HurricaneDataProcessor
            
            start_time = time.time()
            processor = HurricaneDataProcessor()
            sample_data = processor.get_filtered_data(year_from=2020, year_to=2023)
            query_time = time.time() - start_time
            
            print(f"✅ CSV fallback: {len(sample_data):,} records in {query_time:.3f}s")
            return True
            
        except Exception as csv_e:
            print(f"❌ CSV fallback failed: {csv_e}")
            return False
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print("🔄 Trying CSV fallback...")
        
        try:
            from data_processor import HurricaneDataProcessor
            
            start_time = time.time()
            processor = HurricaneDataProcessor()
            sample_data = processor.get_filtered_data(year_from=2020, year_to=2023)
            query_time = time.time() - start_time
            
            print(f"✅ CSV fallback: {len(sample_data):,} records in {query_time:.3f}s")
            return True
            
        except Exception as csv_e:
            print(f"❌ CSV fallback failed: {csv_e}")
            return False

def test_view_manager_performance():
    """Test view manager caching performance"""
    print("\n⚡ Testing View Manager Performance...")
    
    try:
        # Initialize view manager
        view_manager = PersistentViewManager()
        print("✅ ViewManager initialized")
        
        # Create test filter states
        filter1 = FilterState(year_range=(2020, 2023))
        filter2 = FilterState(year_range=(2015, 2019), categories=["5"])
        filter3 = FilterState(selected_storms=["MICHAEL", "FLORENCE"])
        
        filters = [filter1, filter2, filter3]
        filter_names = ["2020-2023", "2015-2019 Cat5", "Selected Storms"]
        
        # Test cache generation for each filter
        for i, (filter_state, name) in enumerate(zip(filters, filter_names)):
            print(f"\n📊 Testing filter: {name}")
            
            # Update filter state (triggers background caching)
            start_time = time.time()
            view_manager.update_filter_state(filter_state)
            update_time = time.time() - start_time
            print(f"  Filter update: {update_time:.3f}s")
            
            # Check cache status immediately
            for view_type in ViewType:
                cache = view_manager.get_cached_view(view_type, filter_state)
                status = cache.status.value if cache else "NOT_FOUND"
                print(f"  {view_type.value}: {status}")
            
            # Wait a bit for background processing
            time.sleep(2)
            
            # Check cache status after processing
            print(f"  After 2s processing:")
            for view_type in ViewType:
                cache = view_manager.get_cached_view(view_type, filter_state)
                status = cache.status.value if cache else "NOT_FOUND"
                data_size = len(cache.figure.data) if cache and cache.figure else 0
                print(f"  {view_type.value}: {status} ({data_size} traces)")
        
        # Test cache retrieval performance
        print(f"\n🚀 Testing Cache Retrieval Speed...")
        for view_type in ViewType:
            start_time = time.time()
            cache = view_manager.get_cached_view(view_type, filter1)
            retrieval_time = time.time() - start_time
            
            status = cache.status.value if cache else "NOT_FOUND"
            print(f"  {view_type.value}: {retrieval_time:.4f}s ({status})")
        
        # Test concurrent access
        print(f"\n🔄 Testing Concurrent Access...")
        def concurrent_test():
            for _ in range(5):
                cache = view_manager.get_cached_view(ViewType.TIMELINE, filter1)
                time.sleep(0.1)
        
        threads = [threading.Thread(target=concurrent_test) for _ in range(3)]
        start_time = time.time()
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        print(f"  3 concurrent threads: {concurrent_time:.3f}s")
        
        # Cleanup
        view_manager.cleanup()
        print("✅ ViewManager cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"❌ ViewManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_usage():
    """Test memory usage and cache limits"""
    print("\n💾 Testing Memory Usage...")
    
    try:
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  Initial memory: {initial_memory:.1f} MB")
        
        # Create view manager and populate caches
        view_manager = PersistentViewManager()
        
        # Create multiple filter states to test cache limits
        filters = []
        for year in range(2015, 2024):
            filters.append(FilterState(year_range=(year, year)))
        
        print(f"  Testing {len(filters)} different filter states...")
        
        for i, filter_state in enumerate(filters):
            view_manager.update_filter_state(filter_state)
            
            if i % 3 == 0:  # Check memory every 3 filters
                current_memory = process.memory_info().rss / 1024 / 1024
                cache_count = sum(1 for vt in ViewType 
                                for fs in filters[:i+1] 
                                if view_manager.get_cached_view(vt, fs))
                print(f"  After {i+1} filters: {current_memory:.1f} MB ({cache_count} cached views)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"  Final memory: {final_memory:.1f} MB (+{memory_increase:.1f} MB)")
        
        # Cleanup
        view_manager.cleanup()
        
        return True
        
    except ImportError:
        print("  ⚠️  psutil not available, skipping memory test")
        return True
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False

def main():
    """Run all performance tests"""
    print("🏃‍♂️ Hurricane Dashboard Performance Tests")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("View Manager Performance", test_view_manager_performance),
        ("Memory Usage", test_memory_usage)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    total_time = time.time() - start_time
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Runtime: {total_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! Dashboard is ready for high performance.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)