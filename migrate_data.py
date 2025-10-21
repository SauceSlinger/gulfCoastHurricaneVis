#!/usr/bin/env python3
"""
Hurricane Data Migration Script
Migrates CSV data to PostgreSQL with data validation and optimization
"""

import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
import re
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from database.config import DATABASE_CONFIG
except ImportError:
    from database.config_template import DATABASE_CONFIG

class HurricaneDataMigrator:
    """Migrate hurricane CSV data to PostgreSQL with optimization"""
    
    def __init__(self, csv_file_path="storms.csv"):
        self.csv_file_path = csv_file_path
        self.logger = self._setup_logging()
        
        # Data validation and transformation rules
        self.gulf_coast_bounds = {
            'lat_min': 24.0, 'lat_max': 31.0,
            'lon_min': -98.0, 'lon_max': -80.0
        }
        
        # Category mapping for consistency
        self.category_mapping = {
            'HU': 'Hurricane',
            'TS': 'Tropical Storm', 
            'TD': 'Tropical Depression',
            'EX': 'Extratropical',
            'SD': 'Subtropical Depression',
            'SS': 'Subtropical Storm'
        }
    
    def _setup_logging(self):
        """Setup logging for migration process"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('migration.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                host=DATABASE_CONFIG['host'],
                port=DATABASE_CONFIG['port'],
                database=DATABASE_CONFIG['database'],
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password']
            )
            self.logger.info("Connected to PostgreSQL database successfully")
            return conn
        
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def load_and_validate_csv(self) -> pd.DataFrame:
        """Load and validate CSV data"""
        self.logger.info(f"Loading CSV data from {self.csv_file_path}")
        
        try:
            # Load CSV with proper data types
            df = pd.read_csv(self.csv_file_path, low_memory=False)
            
            self.logger.info(f"Loaded {len(df)} records from CSV")
            self.logger.info(f"Columns: {list(df.columns)}")
            
            # Data validation and cleaning
            df = self._clean_and_validate_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV data: {e}")
            raise
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate hurricane data"""
        self.logger.info("Cleaning and validating data...")
        
        original_count = len(df)
        
        # Standardize column names (assuming your CSV structure)
        column_mapping = {
            # Map your CSV columns to standard names
            'NAME': 'name',
            'YEAR': 'year', 
            'LAT': 'latitude',
            'LONG': 'longitude',
            'WIND': 'wind_speed',
            'PRESSURE': 'pressure',
            'CAT': 'category',
            'TYPE': 'storm_type',
            'DATE': 'date',
            'TIME': 'time'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Convert data types
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        if 'latitude' in df.columns:
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
            
        if 'longitude' in df.columns:
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
            
        if 'wind_speed' in df.columns:
            df['wind_speed'] = pd.to_numeric(df['wind_speed'], errors='coerce')
            
        if 'pressure' in df.columns:
            df['pressure'] = pd.to_numeric(df['pressure'], errors='coerce')
        
        if 'category' in df.columns:
            df['category'] = pd.to_numeric(df['category'], errors='coerce')
        
        # Remove invalid coordinates
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df = df.dropna(subset=['latitude', 'longitude'])
            df = df[(df['latitude'] >= -90) & (df['latitude'] <= 90)]
            df = df[(df['longitude'] >= -180) & (df['longitude'] <= 180)]
        
        # Remove invalid years
        if 'year' in df.columns:
            df = df[(df['year'] >= 1850) & (df['year'] <= 2030)]
        
        # Add Gulf Coast flag
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df['is_gulf_coast_point'] = (
                (df['latitude'] >= self.gulf_coast_bounds['lat_min']) &
                (df['latitude'] <= self.gulf_coast_bounds['lat_max']) &
                (df['longitude'] >= self.gulf_coast_bounds['lon_min']) &
                (df['longitude'] <= self.gulf_coast_bounds['lon_max'])
            )
        
        # Parse date/time if available
        if 'date' in df.columns:
            try:
                df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')
            except:
                df['parsed_date'] = None
        
        # Clean storm names
        if 'name' in df.columns:
            df['name'] = df['name'].str.strip().str.upper()
            # Remove numeric-only names (likely not real storm names)
            df = df[~df['name'].str.isnumeric()]
        
        cleaned_count = len(df)
        self.logger.info(f"Data validation complete: {original_count} -> {cleaned_count} records ({original_count - cleaned_count} removed)")
        
        return df
    
    def create_storm_records(self, df: pd.DataFrame) -> List[Dict]:
        """Create unique storm records for the storms table"""
        self.logger.info("Creating unique storm records...")
        
        # Group by storm name and year to get unique storms
        storm_groups = df.groupby(['name', 'year']).agg({
            'category': 'max',
            'wind_speed': 'max',
            'pressure': 'min',
            'parsed_date': ['min', 'max'],
            'is_gulf_coast_point': 'any'
        }).reset_index()
        
        # Flatten column names
        storm_groups.columns = [
            'name', 'year', 'max_category', 'max_wind_speed', 'min_pressure',
            'start_date', 'end_date', 'is_gulf_coast'
        ]
        
        # Convert to list of dictionaries
        storms = []
        for _, row in storm_groups.iterrows():
            storm = {
                'name': row['name'],
                'year': int(row['year']) if pd.notna(row['year']) else None,
                'max_category': int(row['max_category']) if pd.notna(row['max_category']) else None,
                'max_wind_speed': float(row['max_wind_speed']) if pd.notna(row['max_wind_speed']) else None,
                'min_pressure': float(row['min_pressure']) if pd.notna(row['min_pressure']) else None,
                'start_date': row['start_date'].date() if pd.notna(row['start_date']) else None,
                'end_date': row['end_date'].date() if pd.notna(row['end_date']) else None,
                'is_gulf_coast': bool(row['is_gulf_coast']) if pd.notna(row['is_gulf_coast']) else False
            }
            storms.append(storm)
        
        self.logger.info(f"Created {len(storms)} unique storm records")
        return storms
    
    def insert_storms(self, conn, storms: List[Dict]) -> Dict[Tuple[str, int], int]:
        """Insert storms into database and return storm_id mapping"""
        self.logger.info(f"Inserting {len(storms)} storms into database...")
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        storm_id_map = {}
        
        try:
            # Insert storms in batches
            insert_query = """
                INSERT INTO storms (name, year, max_category, max_wind_speed, min_pressure, 
                                  start_date, end_date, is_gulf_coast)
                VALUES (%(name)s, %(year)s, %(max_category)s, %(max_wind_speed)s, 
                       %(min_pressure)s, %(start_date)s, %(end_date)s, %(is_gulf_coast)s)
                RETURNING id, name, year
            """
            
            batch_size = 1000
            for i in range(0, len(storms), batch_size):
                batch = storms[i:i + batch_size]
                
                for storm in batch:
                    cursor.execute(insert_query, storm)
                    result = cursor.fetchone()
                    storm_id_map[(result['name'], result['year'])] = result['id']
                
                conn.commit()
                self.logger.info(f"Inserted storms batch {i//batch_size + 1}/{(len(storms)-1)//batch_size + 1}")
            
            self.logger.info(f"Successfully inserted {len(storms)} storms")
            return storm_id_map
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to insert storms: {e}")
            raise
        finally:
            cursor.close()
    
    def insert_storm_points(self, conn, df: pd.DataFrame, storm_id_map: Dict[Tuple[str, int], int]):
        """Insert storm tracking points"""
        self.logger.info(f"Inserting {len(df)} storm points...")
        
        cursor = conn.cursor()
        
        try:
            # Prepare storm points data
            storm_points = []
            
            for _, row in df.iterrows():
                storm_key = (row['name'], int(row['year']))
                storm_id = storm_id_map.get(storm_key)
                
                if storm_id is None:
                    continue
                
                point = {
                    'storm_id': storm_id,
                    'point_date': row['parsed_date'].date() if pd.notna(row['parsed_date']) else None,
                    'point_time': row['parsed_date'].time() if pd.notna(row['parsed_date']) else None,
                    'latitude': float(row['latitude']) if pd.notna(row['latitude']) else None,
                    'longitude': float(row['longitude']) if pd.notna(row['longitude']) else None,
                    'wind_speed': float(row['wind_speed']) if pd.notna(row['wind_speed']) else None,
                    'pressure': float(row['pressure']) if pd.notna(row['pressure']) else None,
                    'category': int(row['category']) if pd.notna(row['category']) else None,
                    'storm_type': row.get('storm_type', None),
                    'is_gulf_coast_point': bool(row['is_gulf_coast_point']) if pd.notna(row['is_gulf_coast_point']) else False
                }
                
                storm_points.append(point)
            
            # Insert in batches for better performance
            insert_query = """
                INSERT INTO storm_points (storm_id, point_date, point_time, latitude, longitude,
                                        wind_speed, pressure, category, storm_type, is_gulf_coast_point)
                VALUES (%(storm_id)s, %(point_date)s, %(point_time)s, %(latitude)s, %(longitude)s,
                       %(wind_speed)s, %(pressure)s, %(category)s, %(storm_type)s, %(is_gulf_coast_point)s)
            """
            
            batch_size = 5000
            for i in range(0, len(storm_points), batch_size):
                batch = storm_points[i:i + batch_size]
                execute_batch(cursor, insert_query, batch, page_size=1000)
                conn.commit()
                
                progress = (i + len(batch)) / len(storm_points) * 100
                self.logger.info(f"Storm points progress: {progress:.1f}% ({i + len(batch)}/{len(storm_points)})")
            
            self.logger.info(f"Successfully inserted {len(storm_points)} storm points")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to insert storm points: {e}")
            raise
        finally:
            cursor.close()
    
    def create_indexes_and_views(self, conn):
        """Create additional indexes and refresh materialized views"""
        self.logger.info("Creating additional indexes and refreshing views...")
        
        cursor = conn.cursor()
        
        try:
            # Refresh materialized views
            cursor.execute("REFRESH MATERIALIZED VIEW dashboard_summary")
            conn.commit()
            
            # Analyze tables for better query planning
            cursor.execute("ANALYZE storms")
            cursor.execute("ANALYZE storm_points")
            conn.commit()
            
            self.logger.info("Database optimization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to optimize database: {e}")
            raise
        finally:
            cursor.close()
    
    def run_migration(self):
        """Run complete migration process"""
        self.logger.info("Starting hurricane data migration...")
        start_time = datetime.now()
        
        try:
            # Load and validate CSV data
            df = self.load_and_validate_csv()
            
            # Connect to database
            conn = self.connect_database()
            
            try:
                # Create unique storm records
                storms = self.create_storm_records(df)
                
                # Insert storms and get ID mapping
                storm_id_map = self.insert_storms(conn, storms)
                
                # Insert storm tracking points
                self.insert_storm_points(conn, df, storm_id_map)
                
                # Optimize database
                self.create_indexes_and_views(conn)
                
                # Final statistics
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM storms")
                storm_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM storm_points")
                point_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT MIN(year), MAX(year) FROM storms")
                year_range = cursor.fetchone()
                
                cursor.close()
                
                duration = datetime.now() - start_time
                
                self.logger.info(f"""
Migration completed successfully!
Duration: {duration}
Final Statistics:
- Storms: {storm_count:,}
- Data Points: {point_count:,}
- Year Range: {year_range[0]} - {year_range[1]}
- Average Points per Storm: {point_count / storm_count:.1f}
                """)
                
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            raise

def main():
    """Main migration function"""
    print("Hurricane Data Migration to PostgreSQL")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "storms.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found!")
        print("Usage: python migrate_data.py [csv_file_path]")
        sys.exit(1)
    
    try:
        migrator = HurricaneDataMigrator(csv_file)
        migrator.run_migration()
        print("\nMigration completed successfully! 🌀")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()