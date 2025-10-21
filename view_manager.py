"""
Persistent View Manager for Hurricane Dashboard
Handles intelligent data caching and view state management for responsive UI
"""

import threading
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from enum import Enum
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
import os

class ViewType(Enum):
    TIMELINE = "timeline"
    MAP = "map" 
    ANALYSIS = "analysis"

class CacheStatus(Enum):
    EMPTY = "empty"
    LOADING = "loading"
    READY = "ready"
    STALE = "stale"
    ERROR = "error"

@dataclass
class FilterState:
    """Represents current filter settings"""
    start_year: int = 1975
    end_year: int = 2021
    categories: List[str] = None
    season_type: str = "All Year"
    geographic_scope: str = "Full Atlantic Basin"
    selected_storms: List[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = ["1", "2", "3", "4", "5", "All Storms"]
        if self.selected_storms is None:
            self.selected_storms = []
    
    def to_cache_key(self) -> str:
        """Generate unique cache key from filter state"""
        filter_dict = asdict(self)
        filter_dict['categories'] = sorted(filter_dict['categories'])
        filter_dict['selected_storms'] = sorted(filter_dict['selected_storms'])
        
        filter_json = json.dumps(filter_dict, sort_keys=True)
        return hashlib.md5(filter_json.encode()).hexdigest()

@dataclass 
class ViewCache:
    """Cached data for a specific view"""
    view_type: ViewType
    filter_key: str
    data: Any = None
    figure: go.Figure = None
    metadata: Dict = None
    created_at: datetime = None
    last_accessed: datetime = None
    status: CacheStatus = CacheStatus.EMPTY
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()

class PersistentViewManager:
    """Manages persistent views with intelligent caching and preloading"""
    
    def __init__(self, data_processor, visualizer, cache_dir="cache"):
        self.data_processor = data_processor
        self.visualizer = visualizer
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory caches for each view type
        self.view_caches: Dict[ViewType, Dict[str, ViewCache]] = {
            ViewType.TIMELINE: {},
            ViewType.MAP: {},
            ViewType.ANALYSIS: {}
        }
        
        # Current filter state
        self.current_filters = FilterState()
        
        # Thread management
        self.background_threads: Dict[str, threading.Thread] = {}
        self.shutdown_event = threading.Event()
        
        # Cache settings
        self.cache_settings = {
            'max_cache_size': 50,  # Maximum cached views per type
            'cache_ttl_hours': 2,  # Cache time-to-live
            'preload_enabled': True,
            'auto_refresh_enabled': True,
            'disk_cache_enabled': True
        }
        
        # Callback for UI updates
        self.update_callbacks: Dict[ViewType, List[Callable]] = {
            ViewType.TIMELINE: [],
            ViewType.MAP: [],
            ViewType.ANALYSIS: []
        }
        
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Load existing disk cache
        self._load_disk_cache()
        
        # Start background management thread
        self._start_background_manager()
    
    def _setup_logging(self):
        """Setup logging for view manager"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - ViewManager - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def register_update_callback(self, view_type: ViewType, callback: Callable):
        """Register callback for view updates"""
        self.update_callbacks[view_type].append(callback)
    
    def update_filters(self, **filter_updates):
        """Update current filter state and trigger cache updates"""
        old_key = self.current_filters.to_cache_key()
        
        # Update filters
        for key, value in filter_updates.items():
            if hasattr(self.current_filters, key):
                setattr(self.current_filters, key, value)
        
        new_key = self.current_filters.to_cache_key()
        
        if old_key != new_key:
            self.logger.info(f"Filters changed: {old_key[:8]} -> {new_key[:8]}")
            
            # Check if we have cached data for new filters
            self._check_cache_availability()
            
            # Start background preloading for new filter state
            if self.cache_settings['preload_enabled']:
                self._start_preloading()
    
    def get_view_data(self, view_type: ViewType, force_refresh=False) -> Optional[ViewCache]:
        """Get cached view data or trigger loading"""
        filter_key = self.current_filters.to_cache_key()
        
        # Check if we have cached data
        if not force_refresh and filter_key in self.view_caches[view_type]:
            cache = self.view_caches[view_type][filter_key]
            
            # Update access time
            cache.last_accessed = datetime.now()
            
            # Check if cache is still valid
            if self._is_cache_valid(cache):
                self.logger.info(f"Cache hit for {view_type.value}: {filter_key[:8]}")
                return cache
            else:
                self.logger.info(f"Cache stale for {view_type.value}: {filter_key[:8]}")
                cache.status = CacheStatus.STALE
        
        # Need to load data
        return self._load_view_data(view_type, filter_key)
    
    def _load_view_data(self, view_type: ViewType, filter_key: str) -> ViewCache:
        """Load view data in background thread"""
        # Create or update cache entry
        if filter_key not in self.view_caches[view_type]:
            self.view_caches[view_type][filter_key] = ViewCache(
                view_type=view_type,
                filter_key=filter_key,
                status=CacheStatus.LOADING
            )
        
        cache = self.view_caches[view_type][filter_key]
        cache.status = CacheStatus.LOADING
        
        # Start background loading
        thread_id = f"{view_type.value}_{filter_key[:8]}"
        if thread_id not in self.background_threads or not self.background_threads[thread_id].is_alive():
            thread = threading.Thread(
                target=self._background_load_view,
                args=(view_type, filter_key),
                daemon=True
            )
            thread.start()
            self.background_threads[thread_id] = thread
        
        return cache
    
    def _background_load_view(self, view_type: ViewType, filter_key: str):
        """Background thread to load view data"""
        try:
            self.logger.info(f"Background loading {view_type.value} for {filter_key[:8]}")
            
            cache = self.view_caches[view_type][filter_key]
            
            # Get filtered data based on current filters
            filtered_data = self._get_filtered_data()
            
            # Generate view-specific data and visualization
            if view_type == ViewType.TIMELINE:
                data = self.data_processor.get_annual_storm_summary(filtered_data)
                figure = self.visualizer.create_timeline_overview(data)
                metadata = {
                    'storm_count': len(filtered_data) if not filtered_data.empty else 0,
                    'year_span': (data['year'].min(), data['year'].max()) if not data.empty else (0, 0),
                    'avg_storms_per_year': data['storm_count'].mean() if not data.empty else 0
                }
                
            elif view_type == ViewType.MAP:
                scope = self.current_filters.geographic_scope
                map_scope = "atlantic" if scope == "Full Atlantic Basin" else "gulf"
                storm_limit = 25 if scope == "Full Atlantic Basin" else 15
                
                storm_tracks = self.data_processor.get_storm_tracks(filtered_data, limit=storm_limit)
                
                if self.current_filters.selected_storms:
                    figure = self.visualizer.create_storm_track_map_with_highlight(
                        storm_tracks, self.current_filters.selected_storms, 
                        title=f"Hurricane Tracks - {scope} (Highlighted)",
                        map_scope=map_scope
                    )
                else:
                    figure = self.visualizer.create_storm_track_map(
                        storm_tracks, title=f"Hurricane Tracks - {scope}", map_scope=map_scope
                    )
                
                data = storm_tracks
                metadata = {
                    'track_count': len(storm_tracks),
                    'geographic_scope': scope,
                    'highlighted_storms': len(self.current_filters.selected_storms)
                }
                
            elif view_type == ViewType.ANALYSIS:
                impact_stats = self.data_processor.get_impact_statistics(filtered_data)
                figure = self.visualizer.create_impact_heatmap(impact_stats)
                data = impact_stats
                metadata = {
                    'total_storms': impact_stats.get('total_storms', 0),
                    'avg_storms_per_year': impact_stats.get('avg_storms_per_year', 0)
                }
            
            # Update cache
            cache.data = data
            cache.figure = figure
            cache.metadata = metadata
            cache.created_at = datetime.now()
            cache.status = CacheStatus.READY
            
            # Save to disk cache
            if self.cache_settings['disk_cache_enabled']:
                self._save_to_disk_cache(cache)
            
            # Notify UI callbacks
            for callback in self.update_callbacks[view_type]:
                try:
                    callback(cache)
                except Exception as e:
                    self.logger.error(f"Callback error for {view_type.value}: {e}")
            
            self.logger.info(f"Successfully loaded {view_type.value} for {filter_key[:8]}")
            
        except Exception as e:
            self.logger.error(f"Error loading {view_type.value}: {e}")
            cache.status = CacheStatus.ERROR
    
    def _get_filtered_data(self) -> pd.DataFrame:
        """Get filtered data based on current filter state"""
        try:
            # Start with year range filter
            data = self.data_processor.filter_by_year_range(
                self.current_filters.start_year,
                self.current_filters.end_year,
                "full_atlantic" if self.current_filters.geographic_scope == "Full Atlantic Basin" else "gulf_coast"
            )
            
            # Apply category filter
            data = self.data_processor.filter_by_categories(self.current_filters.categories, data)
            
            # Apply season filter
            data = self.data_processor.filter_by_season(self.current_filters.season_type, data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting filtered data: {e}")
            return pd.DataFrame()
    
    def _start_preloading(self):
        """Start preloading all views for current filter state"""
        if not self.cache_settings['preload_enabled']:
            return
        
        filter_key = self.current_filters.to_cache_key()
        
        for view_type in ViewType:
            if (filter_key not in self.view_caches[view_type] or 
                self.view_caches[view_type][filter_key].status in [CacheStatus.EMPTY, CacheStatus.STALE]):
                
                self._load_view_data(view_type, filter_key)
    
    def _check_cache_availability(self):
        """Check cache availability for current filters"""
        filter_key = self.current_filters.to_cache_key()
        
        availability = {}
        for view_type in ViewType:
            if filter_key in self.view_caches[view_type]:
                cache = self.view_caches[view_type][filter_key]
                availability[view_type.value] = {
                    'status': cache.status.value,
                    'age_minutes': (datetime.now() - cache.created_at).total_seconds() / 60
                }
            else:
                availability[view_type.value] = {'status': 'not_cached'}
        
        self.logger.info(f"Cache availability for {filter_key[:8]}: {availability}")
        return availability
    
    def _is_cache_valid(self, cache: ViewCache) -> bool:
        """Check if cache entry is still valid"""
        if cache.status != CacheStatus.READY:
            return False
        
        age = datetime.now() - cache.created_at
        max_age = timedelta(hours=self.cache_settings['cache_ttl_hours'])
        
        return age < max_age
    
    def _cleanup_old_caches(self):
        """Remove old cache entries to free memory"""
        max_size = self.cache_settings['max_cache_size']
        
        for view_type in ViewType:
            cache_dict = self.view_caches[view_type]
            
            if len(cache_dict) > max_size:
                # Sort by last accessed time and remove oldest
                sorted_items = sorted(
                    cache_dict.items(),
                    key=lambda x: x[1].last_accessed
                )
                
                # Remove oldest entries
                for key, _ in sorted_items[:-max_size]:
                    del cache_dict[key]
                    self.logger.info(f"Removed old cache entry: {view_type.value}:{key[:8]}")
    
    def _start_background_manager(self):
        """Start background thread for cache management"""
        def background_manager():
            while not self.shutdown_event.is_set():
                try:
                    # Cleanup old caches
                    self._cleanup_old_caches()
                    
                    # Auto-refresh stale caches if enabled
                    if self.cache_settings['auto_refresh_enabled']:
                        self._refresh_stale_caches()
                    
                    # Sleep for 30 seconds
                    self.shutdown_event.wait(30)
                    
                except Exception as e:
                    self.logger.error(f"Background manager error: {e}")
        
        manager_thread = threading.Thread(target=background_manager, daemon=True)
        manager_thread.start()
        self.background_threads['manager'] = manager_thread
    
    def _refresh_stale_caches(self):
        """Refresh caches that are getting stale"""
        current_key = self.current_filters.to_cache_key()
        
        for view_type in ViewType:
            if current_key in self.view_caches[view_type]:
                cache = self.view_caches[view_type][current_key]
                
                # Refresh if cache will be stale in 15 minutes
                age = datetime.now() - cache.created_at
                max_age = timedelta(hours=self.cache_settings['cache_ttl_hours'])
                refresh_threshold = max_age - timedelta(minutes=15)
                
                if age > refresh_threshold and cache.status == CacheStatus.READY:
                    self.logger.info(f"Proactively refreshing {view_type.value} cache")
                    self._load_view_data(view_type, current_key)
    
    def _save_to_disk_cache(self, cache: ViewCache):
        """Save cache to disk for persistence"""
        try:
            cache_file = self.cache_dir / f"{cache.view_type.value}_{cache.filter_key}.pkl"
            
            # Don't save the figure to disk (too large), just metadata
            disk_cache = {
                'view_type': cache.view_type,
                'filter_key': cache.filter_key,
                'data': cache.data,
                'metadata': cache.metadata,
                'created_at': cache.created_at,
                'status': cache.status
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(disk_cache, f)
                
        except Exception as e:
            self.logger.warning(f"Failed to save disk cache: {e}")
    
    def _load_disk_cache(self):
        """Load existing disk cache on startup"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        disk_cache = pickle.load(f)
                    
                    # Check if cache is still valid
                    age = datetime.now() - disk_cache['created_at']
                    if age < timedelta(hours=self.cache_settings['cache_ttl_hours']):
                        
                        cache = ViewCache(
                            view_type=disk_cache['view_type'],
                            filter_key=disk_cache['filter_key'],
                            data=disk_cache['data'],
                            metadata=disk_cache['metadata'],
                            created_at=disk_cache['created_at'],
                            status=CacheStatus.READY  # Will need to regenerate figure
                        )
                        
                        self.view_caches[cache.view_type][cache.filter_key] = cache
                        self.logger.info(f"Loaded disk cache: {cache.view_type.value}:{cache.filter_key[:8]}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load cache file {cache_file}: {e}")
                    # Remove corrupted cache file
                    cache_file.unlink(missing_ok=True)
                    
        except Exception as e:
            self.logger.warning(f"Failed to load disk caches: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'current_filter_key': self.current_filters.to_cache_key(),
            'cache_sizes': {},
            'active_threads': len([t for t in self.background_threads.values() if t.is_alive()]),
            'disk_cache_files': len(list(self.cache_dir.glob("*.pkl")))
        }
        
        for view_type in ViewType:
            cache_dict = self.view_caches[view_type]
            stats['cache_sizes'][view_type.value] = {
                'total': len(cache_dict),
                'ready': len([c for c in cache_dict.values() if c.status == CacheStatus.READY]),
                'loading': len([c for c in cache_dict.values() if c.status == CacheStatus.LOADING]),
                'stale': len([c for c in cache_dict.values() if c.status == CacheStatus.STALE])
            }
        
        return stats
    
    def clear_all_caches(self):
        """Clear all caches"""
        for view_type in ViewType:
            self.view_caches[view_type].clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink(missing_ok=True)
        
        self.logger.info("All caches cleared")
    
    def get_cached_view(self, view_type: ViewType, filter_state: FilterState) -> Optional['ViewCache']:
        """Get cached view for specific filter state"""
        filter_key = filter_state.to_cache_key()
        cache_dict = self.view_caches[view_type]
        
        if filter_key in cache_dict:
            cache = cache_dict[filter_key]
            cache.last_accessed = datetime.now()
            return cache
        
        return None
    
    def update_filter_state(self, filter_state: FilterState):
        """Update current filter state and trigger background refresh"""
        old_key = self.current_filters.to_cache_key()
        self.current_filters = filter_state
        new_key = filter_state.to_cache_key()
        
        if old_key != new_key:
            self.logger.info(f"Filter state updated: {old_key[:8]} -> {new_key[:8]}")
            
            # Start background preloading for new filter state
            if self.cache_settings['preload_enabled']:
                self._start_preloading()
    
    def cleanup(self):
        """Cleanup view manager resources"""
        self.shutdown()
    
    def _start_preloading(self):
        """Start background preloading for current filter state"""
        filter_key = self.current_filters.to_cache_key()
        
        for view_type in ViewType:
            if filter_key not in self.view_caches[view_type]:
                thread_id = f"{view_type.value}_{filter_key[:8]}"
                
                if thread_id not in self.background_threads or not self.background_threads[thread_id].is_alive():
                    thread = threading.Thread(
                        target=self._generate_view_background,
                        args=(view_type, self.current_filters),
                        name=thread_id
                    )
                    thread.daemon = True
                    thread.start()
                    self.background_threads[thread_id] = thread
    
    def _generate_view_background(self, view_type: ViewType, filter_state: FilterState):
        """Generate view in background thread"""
        filter_key = filter_state.to_cache_key()
        
        try:
            # Create cache entry with loading status
            cache = ViewCache(
                view_type=view_type,
                filter_key=filter_key,
                status=CacheStatus.LOADING,
                created_at=datetime.now()
            )
            self.view_caches[view_type][filter_key] = cache
            
            # Generate the actual view data (this would need actual implementation)
            # For now, just mark as ready after a short delay
            time.sleep(0.5)  # Simulate work
            
            cache.status = CacheStatus.READY
            cache.data_ready = True
            
            # Notify callbacks
            for callback in self.update_callbacks[view_type]:
                try:
                    callback(cache)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Background view generation failed: {e}")
            if filter_key in self.view_caches[view_type]:
                self.view_caches[view_type][filter_key].status = CacheStatus.ERROR
    
    def _check_cache_availability(self):
        """Check cache availability for current filters"""
        filter_key = self.current_filters.to_cache_key()
        
        for view_type in ViewType:
            if filter_key in self.view_caches[view_type]:
                cache = self.view_caches[view_type][filter_key]
                self.logger.info(f"Cache available for {view_type.value}: {cache.status.value}")
            else:
                self.logger.info(f"No cache for {view_type.value}")
    
    def _is_cache_valid(self, cache: 'ViewCache') -> bool:
        """Check if cache is still valid"""
        if cache.status != CacheStatus.READY:
            return False
        
        ttl_hours = self.cache_settings['cache_ttl_hours']
        expiry_time = cache.created_at + timedelta(hours=ttl_hours)
        
        return datetime.now() < expiry_time
    
    def _start_background_manager(self):
        """Start background cache management thread"""
        def manage_cache():
            while not self.shutdown_event.is_set():
                try:
                    self._cleanup_expired_cache()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    self.logger.error(f"Cache management error: {e}")
                    time.sleep(60)  # Wait before retrying
        
        manager_thread = threading.Thread(target=manage_cache, name="CacheManager")
        manager_thread.daemon = True
        manager_thread.start()
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.now()
        ttl_hours = self.cache_settings['cache_ttl_hours']
        
        for view_type in ViewType:
            cache_dict = self.view_caches[view_type]
            expired_keys = []
            
            for key, cache in cache_dict.items():
                if current_time - cache.created_at > timedelta(hours=ttl_hours):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del cache_dict[key]
                self.logger.info(f"Removed expired cache: {view_type.value}:{key[:8]}")


# ViewCache class definition
@dataclass 
class ViewCache:
    """Represents a cached view with metadata"""
    view_type: ViewType
    filter_key: str
    status: CacheStatus = CacheStatus.EMPTY
    figure: Optional[go.Figure] = None
    metadata: Optional[Dict] = None
    created_at: datetime = None
    last_accessed: datetime = None
    data_ready: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def shutdown(self):
        """Shutdown view manager and background threads"""
        self.shutdown_event.set()
        
        # Wait for background threads to complete
        for thread in self.background_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("View manager shutdown complete")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.shutdown()