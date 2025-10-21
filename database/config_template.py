# Hurricane Dashboard Database Configuration
# Copy this to config.py and update with your database credentials

# PostgreSQL Database Configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'hurricane_data',
    'user': 'hurricane_app',
    'password': 'your_password_here',
    
    # Connection pool settings for performance
    'minconn': 1,
    'maxconn': 20,
    
    # Connection timeout settings
    'connect_timeout': 10,
    'command_timeout': 30,
}

# Cache configuration (for in-memory caching)
CACHE_CONFIG = {
    'enabled': True,
    'max_size': 1000,  # Maximum number of cached queries
    'ttl': 300,        # Time to live in seconds (5 minutes)
}

# Performance settings
PERFORMANCE_CONFIG = {
    'batch_size': 1000,     # Records to process in batches
    'query_limit': 50000,   # Maximum records per query
    'async_enabled': True,  # Enable async database operations
    'prefetch_size': 100,   # Records to prefetch
}

# Dashboard settings optimized for database performance
DASHBOARD_CONFIG = {
    'default_storm_limit': 25,
    'max_storm_limit': 100,
    'default_year_range': (2000, 2021),  # Reduced default range for faster loading
    'enable_real_time_search': True,
    'search_debounce_ms': 300,  # Delay search queries to avoid overwhelming DB
}

# Data loading optimization
DATA_LOADING_CONFIG = {
    'use_prepared_statements': True,
    'enable_query_caching': True,
    'preload_common_queries': True,
    'background_refresh_interval': 3600,  # Refresh cached data every hour
}

# Development/Debug settings
DEBUG_CONFIG = {
    'log_queries': False,
    'log_performance': True,
    'show_query_time': True,
    'profile_queries': False,
}