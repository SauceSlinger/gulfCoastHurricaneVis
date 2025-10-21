"""
High-Performance Hurricane Database Manager
Provides fast, optimized access to hurricane data using PostgreSQL
"""

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor, execute_batch
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import threading
import time
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager
import json

# Try to import config, fall back to template if not available
try:
    from database.config import DATABASE_CONFIG, CACHE_CONFIG, PERFORMANCE_CONFIG
except ImportError:
    from database.config_template import DATABASE_CONFIG, CACHE_CONFIG, PERFORMANCE_CONFIG

class QueryCache:
    """Simple in-memory cache for database queries"""
    
    def __init__(self, max_size=1000, ttl=300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.RLock()
    
    def _generate_key(self, query, params=None):
        """Generate cache key from query and parameters"""
        if params:
            return f"{query}:{json.dumps(params, sort_keys=True)}"
        return query
    
    def get(self, query, params=None):
        """Get cached query result"""
        key = self._generate_key(query, params)
        
        with self.lock:
            if key in self.cache:
                # Check if expired
                if time.time() - self.access_times[key] > self.ttl:
                    del self.cache[key]
                    del self.access_times[key]
                    return None
                
                self.access_times[key] = time.time()
                return self.cache[key]
        
        return None
    
    def set(self, query, params, result):
        """Cache query result"""
        key = self._generate_key(query, params)
        
        with self.lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), 
                               key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = result
            self.access_times[key] = time.time()
    
    def clear(self):
        """Clear all cached data"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()

class HurricaneDatabaseManager:
    """High-performance database manager for hurricane data"""
    
    def __init__(self, config=None):
        """Initialize database manager with connection pooling and caching"""
        self.config = config or DATABASE_CONFIG
        self.pool = None
        self.cache = QueryCache(
            max_size=CACHE_CONFIG.get('max_size', 1000),
            ttl=CACHE_CONFIG.get('ttl', 300)
        ) if CACHE_CONFIG.get('enabled', True) else None
        
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._initialize_connection_pool()
        
        # Pre-compiled queries for better performance
        self._prepared_queries = {}
        self._setup_prepared_queries()
    
    def _setup_logging(self):
        """Setup performance logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.get('minconn', 1),
                maxconn=self.config.get('maxconn', 20),
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                cursor_factory=RealDictCursor
            )
            self.logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool with proper cleanup"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def _setup_prepared_queries(self):
        """Setup commonly used prepared queries"""
        self._prepared_queries = {
            'annual_summary': """
                SELECT year, storm_count, gulf_coast_storms, avg_max_wind, 
                       highest_wind, major_hurricanes, cat5_storms
                FROM annual_storm_summary 
                WHERE year BETWEEN %s AND %s 
                ORDER BY year
            """,
            
            'storms_by_filters': """
                SELECT s.id, s.name, s.year, s.max_category, s.max_wind_speed, 
                       s.min_pressure, s.is_gulf_coast
                FROM storms s 
                WHERE s.year BETWEEN %s AND %s
                AND (%s = '' OR s.max_category = ANY(%s))
                AND (%s = false OR s.is_gulf_coast = %s)
                ORDER BY s.year DESC, s.max_wind_speed DESC
                LIMIT %s
            """,
            
            'storm_tracks': """
                SELECT s.name, s.year, s.max_category, s.max_wind_speed,
                       array_agg(sp.latitude ORDER BY sp.point_date) as lats,
                       array_agg(sp.longitude ORDER BY sp.point_date) as lons,
                       array_agg(sp.wind_speed ORDER BY sp.point_date) as winds,
                       array_agg(sp.category ORDER BY sp.point_date) as categories
                FROM storms s
                JOIN storm_points sp ON s.id = sp.storm_id
                WHERE s.id = ANY(%s)
                GROUP BY s.id, s.name, s.year, s.max_category, s.max_wind_speed
                ORDER BY s.max_wind_speed DESC
            """,
            
            'geographic_impact': """
                SELECT lat_zone, lon_zone, point_count, storm_count, 
                       avg_wind_speed, max_wind_speed, max_category
                FROM geographic_impact_zones
                WHERE (%s = false OR EXISTS (
                    SELECT 1 FROM storm_points sp 
                    JOIN storms st ON sp.storm_id = st.id 
                    WHERE ROUND(sp.latitude::numeric, 1) = lat_zone 
                    AND ROUND(sp.longitude::numeric, 1) = lon_zone 
                    AND st.is_gulf_coast = true
                ))
                ORDER BY storm_count DESC, max_wind_speed DESC
                LIMIT %s
            """,
            
            'monthly_activity': """
                SELECT month, year, active_storms, avg_wind_speed, 
                       max_wind_speed, major_hurricane_points
                FROM monthly_storm_activity 
                WHERE year BETWEEN %s AND %s
                ORDER BY year, month
            """,
            
            'storm_search': """
                SELECT s.id, s.name, s.year, s.max_category, s.max_wind_speed, 
                       s.min_pressure, s.is_gulf_coast
                FROM storms s 
                WHERE (LOWER(s.name) LIKE LOWER(%s) OR s.year::text LIKE %s)
                AND s.year BETWEEN %s AND %s
                ORDER BY s.year DESC, s.max_wind_speed DESC
                LIMIT %s
            """
        }
    
    def execute_query(self, query, params=None, use_cache=True):
        """Execute query with caching and performance monitoring"""
        start_time = time.time()
        
        # Check cache first
        if use_cache and self.cache:
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                self.logger.info(f"Query served from cache in {time.time() - start_time:.3f}s")
                return cached_result
        
        # Execute query
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchall()
                    
                    # Convert to list of dicts for consistency
                    result_list = [dict(row) for row in result]
                    
                    # Cache the result
                    if use_cache and self.cache:
                        self.cache.set(query, params, result_list)
                    
                    execution_time = time.time() - start_time
                    self.logger.info(f"Query executed in {execution_time:.3f}s, returned {len(result_list)} rows")
                    
                    return result_list
                    
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def get_annual_storm_summary(self, start_year=1975, end_year=2021, gulf_coast_only=False):
        """Get annual storm summary with optimized query"""
        query = self._prepared_queries['annual_summary']
        params = (start_year, end_year)
        
        results = self.execute_query(query, params)
        
        if gulf_coast_only:
            # Filter to only Gulf Coast data
            results = [
                {**row, 'storm_count': row['gulf_coast_storms']}
                for row in results
            ]
        
        return pd.DataFrame(results) if results else pd.DataFrame()
    
    def get_filtered_storms(self, start_year=1975, end_year=2021, 
                           categories=None, gulf_coast_only=False, limit=50):
        """Get storms matching filters with optimized query"""
        # Prepare category filter
        if categories and 'All Storms' not in categories:
            category_list = [int(cat) for cat in categories if cat.isdigit()]
            has_categories = True
        else:
            category_list = []
            has_categories = False
        
        query = self._prepared_queries['storms_by_filters']
        params = (
            start_year, end_year,
            '' if not has_categories else 'has_cats',
            category_list,
            gulf_coast_only, gulf_coast_only,
            limit
        )
        
        results = self.execute_query(query, params)
        return pd.DataFrame(results) if results else pd.DataFrame()
    
    def get_storm_tracks(self, storm_ids, limit=25):
        """Get storm track data for visualization"""
        if not storm_ids:
            return {}
        
        # Limit the number of storms for performance
        limited_ids = storm_ids[:limit]
        
        query = self._prepared_queries['storm_tracks']
        params = (limited_ids,)
        
        results = self.execute_query(query, params)
        
        # Convert to expected format
        tracks = {}
        for i, row in enumerate(results):
            track_id = f"{row['name']}_{row['year']}"
            tracks[track_id] = {
                'name': row['name'],
                'year': row['year'],
                'category': row['max_category'],
                'max_wind': row['max_wind_speed'],
                'lats': [lat for lat in row['lats'] if lat is not None],
                'lons': [lon for lon in row['lons'] if lon is not None],
                'winds': [wind for wind in row['winds'] if wind is not None],
                'categories': [cat for cat in row['categories'] if cat is not None]
            }
        
        return tracks
    
    def get_impact_statistics(self, start_year=1975, end_year=2021, gulf_coast_only=False):
        """Get geographic impact statistics"""
        query = self._prepared_queries['geographic_impact']
        params = (gulf_coast_only, 1000)  # Limit to top 1000 zones
        
        results = self.execute_query(query, params)
        
        if not results:
            return {}
        
        # Calculate summary statistics
        total_storms = sum(row['storm_count'] for row in results)
        avg_storms_per_year = total_storms / max(1, end_year - start_year + 1)
        
        return {
            'total_storms': total_storms,
            'avg_storms_per_year': avg_storms_per_year,
            'impact_zones': results,
            'most_active_zone': max(results, key=lambda x: x['storm_count']) if results else None
        }
    
    def get_seasonal_data(self, start_year=1975, end_year=2021):
        """Get monthly/seasonal activity data"""
        query = self._prepared_queries['monthly_activity']
        params = (start_year, end_year)
        
        results = self.execute_query(query, params)
        return pd.DataFrame(results) if results else pd.DataFrame()
    
    def search_storms(self, search_term, start_year=1975, end_year=2021, limit=50):
        """Search storms by name or year"""
        # Prepare search patterns
        name_pattern = f"%{search_term}%"
        year_pattern = f"%{search_term}%"
        
        query = self._prepared_queries['storm_search']
        params = (name_pattern, year_pattern, start_year, end_year, limit)
        
        results = self.execute_query(query, params)
        return results
    
    def get_dashboard_summary(self):
        """Get dashboard summary statistics"""
        query = "SELECT metric, value, description FROM dashboard_summary"
        results = self.execute_query(query)
        
        return {row['metric']: {'value': row['value'], 'description': row['description']} 
                for row in results}
    
    def refresh_materialized_views(self):
        """Refresh materialized views for updated statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT refresh_dashboard_summary()")
                    conn.commit()
            
            # Clear cache to ensure fresh data
            if self.cache:
                self.cache.clear()
            
            self.logger.info("Materialized views refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh materialized views: {e}")
            raise
    
    def get_connection_stats(self):
        """Get connection pool statistics"""
        if self.pool:
            return {
                'total_connections': self.pool.maxconn,
                'available_connections': len(self.pool._pool),
                'used_connections': self.pool.maxconn - len(self.pool._pool)
            }
        return {}
    
    def close_pool(self):
        """Close all database connections"""
        if self.pool:
            self.pool.closeall()
            self.logger.info("Database connection pool closed")

# Singleton instance for global access
_db_manager = None

def get_db_manager():
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = HurricaneDatabaseManager()
    return _db_manager

def close_db_manager():
    """Close database manager singleton"""
    global _db_manager
    if _db_manager:
        _db_manager.close_pool()
        _db_manager = None