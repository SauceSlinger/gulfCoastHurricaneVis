-- Hurricane Data PostgreSQL Schema
-- Optimized for fast queries and dashboard performance

-- Create database (run this as superuser first)
-- CREATE DATABASE hurricane_data;

-- Create extension for geographic data types (optional, for future geo-queries)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Main storms table for unique storm identification and metadata
CREATE TABLE storms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    basin VARCHAR(10) DEFAULT 'Atlantic',
    max_category INTEGER,
    max_wind_speed NUMERIC(6,2),
    min_pressure NUMERIC(8,2),
    start_date DATE,
    end_date DATE,
    peak_intensity_date DATE,
    is_gulf_coast BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Storm data points table for tracking positions and intensities
CREATE TABLE storm_points (
    id SERIAL PRIMARY KEY,
    storm_id INTEGER REFERENCES storms(id) ON DELETE CASCADE,
    point_date DATE,
    point_time TIME,
    latitude NUMERIC(8,5) NOT NULL,
    longitude NUMERIC(9,5) NOT NULL,
    wind_speed NUMERIC(6,2),
    pressure NUMERIC(8,2),
    category INTEGER,
    storm_type VARCHAR(20), -- 'HU', 'TS', 'TD', etc.
    distance_to_land NUMERIC(8,2), -- km to nearest land
    is_gulf_coast_point BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create optimized indexes for fast queries
CREATE INDEX idx_storms_name_year ON storms(name, year);
CREATE INDEX idx_storms_year ON storms(year);
CREATE INDEX idx_storms_max_category ON storms(max_category);
CREATE INDEX idx_storms_gulf_coast ON storms(is_gulf_coast);
CREATE INDEX idx_storms_max_wind ON storms(max_wind_speed);

CREATE INDEX idx_storm_points_storm_id ON storm_points(storm_id);
CREATE INDEX idx_storm_points_date ON storm_points(point_date);
CREATE INDEX idx_storm_points_category ON storm_points(category);
CREATE INDEX idx_storm_points_location ON storm_points(latitude, longitude);
CREATE INDEX idx_storm_points_gulf_coast ON storm_points(is_gulf_coast_point);
CREATE INDEX idx_storm_points_wind ON storm_points(wind_speed);

-- Composite indexes for common query patterns
CREATE INDEX idx_storms_year_category ON storms(year, max_category);
CREATE INDEX idx_storms_name_year_category ON storms(name, year, max_category);
CREATE INDEX idx_storm_points_storm_date ON storm_points(storm_id, point_date);

-- Views for common dashboard queries

-- Annual storm summary view
CREATE OR REPLACE VIEW annual_storm_summary AS
SELECT 
    year,
    COUNT(*) as storm_count,
    COUNT(*) FILTER (WHERE is_gulf_coast = true) as gulf_coast_storms,
    AVG(max_wind_speed) as avg_max_wind,
    MAX(max_wind_speed) as highest_wind,
    AVG(min_pressure) as avg_min_pressure,
    MIN(min_pressure) as lowest_pressure,
    COUNT(*) FILTER (WHERE max_category >= 3) as major_hurricanes,
    COUNT(*) FILTER (WHERE max_category = 5) as cat5_storms
FROM storms 
GROUP BY year 
ORDER BY year;

-- Storm tracks summary view
CREATE OR REPLACE VIEW storm_tracks_summary AS
SELECT 
    s.id,
    s.name,
    s.year,
    s.max_category,
    s.max_wind_speed,
    s.min_pressure,
    s.is_gulf_coast,
    COUNT(sp.id) as track_points,
    MIN(sp.point_date) as start_date,
    MAX(sp.point_date) as end_date,
    MIN(sp.latitude) as min_lat,
    MAX(sp.latitude) as max_lat,
    MIN(sp.longitude) as min_lon,
    MAX(sp.longitude) as max_lon
FROM storms s
LEFT JOIN storm_points sp ON s.id = sp.storm_id
GROUP BY s.id, s.name, s.year, s.max_category, s.max_wind_speed, s.min_pressure, s.is_gulf_coast;

-- Monthly activity view for seasonal analysis
CREATE OR REPLACE VIEW monthly_storm_activity AS
SELECT 
    EXTRACT(MONTH FROM sp.point_date) as month,
    EXTRACT(YEAR FROM sp.point_date) as year,
    COUNT(DISTINCT s.id) as active_storms,
    AVG(sp.wind_speed) as avg_wind_speed,
    MAX(sp.wind_speed) as max_wind_speed,
    COUNT(*) FILTER (WHERE sp.category >= 3) as major_hurricane_points
FROM storms s
JOIN storm_points sp ON s.id = sp.storm_id
WHERE sp.point_date IS NOT NULL
GROUP BY EXTRACT(MONTH FROM sp.point_date), EXTRACT(YEAR FROM sp.point_date)
ORDER BY year, month;

-- Geographic impact zones view
CREATE OR REPLACE VIEW geographic_impact_zones AS
SELECT 
    ROUND(latitude::numeric, 1) as lat_zone,
    ROUND(longitude::numeric, 1) as lon_zone,
    COUNT(*) as point_count,
    COUNT(DISTINCT storm_id) as storm_count,
    AVG(wind_speed) as avg_wind_speed,
    MAX(wind_speed) as max_wind_speed,
    AVG(category) as avg_category,
    MAX(category) as max_category
FROM storm_points 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
GROUP BY ROUND(latitude::numeric, 1), ROUND(longitude::numeric, 1)
HAVING COUNT(*) >= 5  -- Only zones with significant activity
ORDER BY storm_count DESC, max_wind_speed DESC;

-- Create function to update storm metadata when points are added
CREATE OR REPLACE FUNCTION update_storm_metadata()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the parent storm record with computed statistics
    UPDATE storms 
    SET 
        max_wind_speed = (
            SELECT MAX(wind_speed) 
            FROM storm_points 
            WHERE storm_id = NEW.storm_id
        ),
        min_pressure = (
            SELECT MIN(pressure) 
            FROM storm_points 
            WHERE storm_id = NEW.storm_id AND pressure IS NOT NULL
        ),
        max_category = (
            SELECT MAX(category) 
            FROM storm_points 
            WHERE storm_id = NEW.storm_id AND category IS NOT NULL
        ),
        start_date = (
            SELECT MIN(point_date) 
            FROM storm_points 
            WHERE storm_id = NEW.storm_id AND point_date IS NOT NULL
        ),
        end_date = (
            SELECT MAX(point_date) 
            FROM storm_points 
            WHERE storm_id = NEW.storm_id AND point_date IS NOT NULL
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.storm_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update storm metadata
CREATE TRIGGER trigger_update_storm_metadata
    AFTER INSERT OR UPDATE ON storm_points
    FOR EACH ROW
    EXECUTE FUNCTION update_storm_metadata();

-- Performance optimization: Create materialized views for dashboard summary data
CREATE MATERIALIZED VIEW dashboard_summary AS
SELECT 
    'total_storms' as metric,
    COUNT(*)::text as value,
    'Total storms in database' as description
FROM storms
UNION ALL
SELECT 
    'gulf_coast_storms' as metric,
    COUNT(*)::text as value,
    'Storms affecting Gulf Coast' as description  
FROM storms WHERE is_gulf_coast = true
UNION ALL
SELECT 
    'total_data_points' as metric,
    COUNT(*)::text as value,
    'Total tracking data points' as description
FROM storm_points
UNION ALL
SELECT 
    'year_range' as metric,
    MIN(year) || ' - ' || MAX(year) as value,
    'Data coverage period' as description
FROM storms
UNION ALL
SELECT 
    'strongest_storm' as metric,
    name || ' (' || year || ')' as value,
    'Highest recorded wind speed: ' || max_wind_speed || ' mph' as description
FROM storms 
WHERE max_wind_speed = (SELECT MAX(max_wind_speed) FROM storms);

-- Create index on materialized view
CREATE UNIQUE INDEX idx_dashboard_summary_metric ON dashboard_summary(metric);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_dashboard_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL ON DATABASE hurricane_data TO hurricane_app;
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO hurricane_app;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO hurricane_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO hurricane_app;