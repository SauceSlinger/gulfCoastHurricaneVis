"""
Data Processing Module for Gulf Coast Hurricane Visualization
Handles data cleaning, filtering, and preparation for visualizations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

class HurricaneDataProcessor:
    """Process and filter hurricane data for Gulf Coast analysis"""
    
    # Gulf Coast boundaries (approximate)
    GULF_COAST_BOUNDS = {
        'lat_min': 24.0,   # Southern tip of Florida
        'lat_max': 31.0,   # Northern Gulf Coast
        'lon_min': -98.0,  # Texas coast
        'lon_max': -80.0   # Florida coast
    }
    
    # Full Atlantic Basin boundaries (for comprehensive view)
    ATLANTIC_BASIN_BOUNDS = {
        'lat_min': 7.0,    # Caribbean/Tropical Atlantic
        'lat_max': 70.7,   # North Atlantic/Canada
        'lon_min': -109.3, # Eastern Pacific influence
        'lon_max': 13.5    # Eastern Atlantic/Africa
    }
    
    # Hurricane season months
    HURRICANE_SEASON = {
        'peak': [8, 9, 10],      # August, September, October
        'early': [6, 7],         # June, July
        'late': [11],            # November
        'all': list(range(6, 12)) # June through November
    }
    
    def __init__(self, csv_file: str = "storms.csv"):
        """Initialize the data processor"""
        self.raw_data = None
        self.processed_data = None
        self.gulf_coast_data = None
        self.full_atlantic_data = None  # New: full dataset
        self.load_data(csv_file)
    
    def load_data(self, csv_file: str) -> bool:
        """Load hurricane data from CSV file"""
        try:
            self.raw_data = pd.read_csv(csv_file)
            print(f"Loaded {len(self.raw_data)} hurricane records")
            
            # Clean and prepare the data
            self.clean_data()
            self.filter_gulf_coast_storms()
            self.prepare_full_atlantic_data()
            return True
            
        except FileNotFoundError:
            print(f"Error: Could not find {csv_file}")
            return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def clean_data(self):
        """Clean and standardize the hurricane data"""
        if self.raw_data is None:
            return
        
        # Make a copy for processing
        self.processed_data = self.raw_data.copy()
        
        # Standardize column names
        if 'Unnamed: 0' in self.processed_data.columns:
            self.processed_data = self.processed_data.drop('Unnamed: 0', axis=1)
        
        # Convert data types
        self.processed_data['year'] = pd.to_numeric(self.processed_data['year'], errors='coerce')
        self.processed_data['month'] = pd.to_numeric(self.processed_data['month'], errors='coerce')
        self.processed_data['day'] = pd.to_numeric(self.processed_data['day'], errors='coerce')
        self.processed_data['hour'] = pd.to_numeric(self.processed_data['hour'], errors='coerce')
        self.processed_data['lat'] = pd.to_numeric(self.processed_data['lat'], errors='coerce')
        self.processed_data['long'] = pd.to_numeric(self.processed_data['long'], errors='coerce')
        self.processed_data['wind'] = pd.to_numeric(self.processed_data['wind'], errors='coerce')
        self.processed_data['pressure'] = pd.to_numeric(self.processed_data['pressure'], errors='coerce')
        self.processed_data['category'] = pd.to_numeric(self.processed_data['category'], errors='coerce')
        
        # Create datetime column
        self.processed_data['datetime'] = pd.to_datetime(
            self.processed_data[['year', 'month', 'day', 'hour']], 
            errors='coerce'
        )
        
        # Clean up status field
        self.processed_data['status'] = self.processed_data['status'].fillna('unknown')
        
        print(f"Data cleaned. {len(self.processed_data)} records processed.")
    
    def calculate_storm_metrics(self):
        """Calculate additional metrics for each storm"""
        if self.processed_data is None:
            return
        
        # Initialize new columns with default values
        self.processed_data = self.processed_data.copy()
        self.processed_data['distance_traveled_km'] = 0.0
        self.processed_data['storm_duration_hours'] = 0.0
        self.processed_data['max_wind_in_storm'] = 0.0
        self.processed_data['min_pressure_in_storm'] = 1100.0  # Use reasonable default instead of inf
        
        # Group by storm name and year to handle storms with same names in different years
        storm_groups = self.processed_data.groupby(['name', 'year'])
        
        for (storm_name, year), group in storm_groups:
            if len(group) < 2:
                continue
                
            try:
                # Sort by datetime
                group_sorted = group.sort_values('datetime').copy()
                indices = group_sorted.index.tolist()
                
                # Calculate total distance traveled
                total_distance = 0
                for i in range(1, len(group_sorted)):
                    prev_row = group_sorted.iloc[i-1]
                    curr_row = group_sorted.iloc[i]
                    
                    lat1, lon1 = prev_row['lat'], prev_row['long']
                    lat2, lon2 = curr_row['lat'], curr_row['long']
                    
                    if pd.notna([lat1, lon1, lat2, lon2]).all():
                        distance = self.haversine_distance(lat1, lon1, lat2, lon2)
                        total_distance += distance
                        
                        # Update the distance for this point
                        current_index = indices[i]
                        self.processed_data.at[current_index, 'distance_traveled_km'] = total_distance
                
                # Calculate storm duration
                start_time = group_sorted['datetime'].min()
                end_time = group_sorted['datetime'].max()
                
                if pd.notna(start_time) and pd.notna(end_time):
                    duration = (end_time - start_time).total_seconds() / 3600  # Convert to hours
                    # Update all points for this storm
                    for idx in indices:
                        self.processed_data.at[idx, 'storm_duration_hours'] = duration
                
                # Set max wind speed and min pressure for the entire storm
                max_wind = group_sorted['wind'].max()
                min_pressure = group_sorted['pressure'].min()
                
                if pd.notna(max_wind):
                    for idx in indices:
                        self.processed_data.at[idx, 'max_wind_in_storm'] = max_wind
                        
                if pd.notna(min_pressure):
                    for idx in indices:
                        self.processed_data.at[idx, 'min_pressure_in_storm'] = min_pressure
                        
            except Exception as e:
                print(f"Warning: Could not calculate metrics for storm {storm_name} ({year}): {e}")
                continue
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points in kilometers"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def filter_gulf_coast_storms(self):
        """Filter storms that affected the Gulf Coast region"""
        if self.processed_data is None:
            return
        
        # Filter for storms that passed through Gulf Coast region
        gulf_mask = (
            (self.processed_data['lat'] >= self.GULF_COAST_BOUNDS['lat_min']) &
            (self.processed_data['lat'] <= self.GULF_COAST_BOUNDS['lat_max']) &
            (self.processed_data['long'] >= self.GULF_COAST_BOUNDS['lon_min']) &
            (self.processed_data['long'] <= self.GULF_COAST_BOUNDS['lon_max'])
        )
        
        # Get storm names that have at least one point in Gulf Coast region
        gulf_storm_names = self.processed_data[gulf_mask].groupby(['name', 'year']).size().index
        
        # Include all data points for these storms (not just Gulf Coast points)
        self.gulf_coast_data = self.processed_data[
            self.processed_data.set_index(['name', 'year']).index.isin(gulf_storm_names)
        ].copy()
        
        print(f"Filtered to {len(self.gulf_coast_data)} records from Gulf Coast storms")
        print(f"Total Gulf Coast storms: {len(gulf_storm_names)}")
    
    def prepare_full_atlantic_data(self):
        """Prepare full Atlantic basin dataset for comprehensive analysis"""
        if self.processed_data is None:
            return
        
        # Use the entire cleaned dataset for full Atlantic view
        self.full_atlantic_data = self.processed_data.copy()
        
        print(f"Full Atlantic dataset: {len(self.full_atlantic_data)} records")
        print(f"Total Atlantic storms: {self.full_atlantic_data.groupby(['name', 'year']).size().count()}")
        print(f"Geographic scope: {self.full_atlantic_data['lat'].min():.1f}° to {self.full_atlantic_data['lat'].max():.1f}°N, {self.full_atlantic_data['long'].min():.1f}° to {self.full_atlantic_data['long'].max():.1f}°W")
    
    def get_dataset_for_analysis(self, analysis_type: str = "gulf_coast") -> pd.DataFrame:
        """Get the appropriate dataset based on analysis type"""
        if analysis_type == "full_atlantic" and self.full_atlantic_data is not None:
            return self.full_atlantic_data
        elif analysis_type == "gulf_coast" and self.gulf_coast_data is not None:
            return self.gulf_coast_data
        else:
            return pd.DataFrame()
    
    def filter_by_year_range(self, start_year: int, end_year: int, dataset_type: str = "gulf_coast") -> pd.DataFrame:
        """Filter data by year range from specified dataset"""
        base_data = self.get_dataset_for_analysis(dataset_type)
        
        if base_data.empty:
            return pd.DataFrame()
        
        return base_data[
            (base_data['year'] >= start_year) &
            (base_data['year'] <= end_year)
        ].copy()
    
    def filter_by_categories(self, categories: List[str], data: pd.DataFrame = None) -> pd.DataFrame:
        """Filter data by hurricane categories (updated to work with any dataset)"""
        if data is None:
            data = self.gulf_coast_data
            
        if data is None or data.empty:
            return pd.DataFrame()
        
        # If "All Storms" is selected, return all data
        if "All Storms" in categories:
            return data
        
        # Convert category strings to numbers
        numeric_categories = []
        for cat in categories:
            if cat.isdigit():
                numeric_categories.append(float(cat))
        
        if not numeric_categories:
            return pd.DataFrame()  # No valid categories selected
        
        # Filter by categories - include hurricanes of specified categories
        # Also include tropical storms and depressions as they may strengthen
        cat_mask = data['category'].isin(numeric_categories)
        
        # Include non-hurricane storms (they're part of the story)
        non_hurricane_mask = data['status'].isin([
            'tropical storm', 'tropical depression', 'subtropical storm'
        ])
        
        # Combine the conditions
        final_mask = cat_mask | non_hurricane_mask
        
        return data[final_mask]
    
    def filter_by_season(self, season_type: str, data: pd.DataFrame = None) -> pd.DataFrame:
        """Filter data by hurricane season period (updated to work with any dataset)"""
        if data is None:
            data = self.gulf_coast_data
            
        if data is None or data.empty:
            return pd.DataFrame()
        
        season_months = {
            "All Year": list(range(1, 13)),
            "Peak Season (Aug-Oct)": self.HURRICANE_SEASON['peak'],
            "Early Season (Jun-Jul)": self.HURRICANE_SEASON['early'],
            "Late Season (Nov)": self.HURRICANE_SEASON['late']
        }
        
        months = season_months.get(season_type, list(range(1, 13)))
        return data[data['month'].isin(months)].copy()
    
    def get_annual_storm_summary(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """Get annual summary statistics for storms"""
        if data is None:
            data = self.gulf_coast_data
        
        if data is None or len(data) == 0:
            return pd.DataFrame()
        
        # Group by year and storm name to get unique storms per year
        annual_stats = data.groupby('year').agg({
            'name': 'nunique',  # Number of unique storms
            'wind': ['max', 'mean'],  # Max and mean wind speed
            'pressure': ['min', 'mean'],  # Min and mean pressure
            'category': 'max',  # Highest category reached
        }).reset_index()
        
        # Flatten column names
        annual_stats.columns = [
            'year', 'storm_count', 'max_wind', 'mean_wind',
            'min_pressure', 'mean_pressure', 'max_category'
        ]
        
        return annual_stats
    
    def get_landfall_data(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """Identify potential landfall points (storms crossing from water to land)"""
        if data is None:
            data = self.gulf_coast_data
        
        if data is None or len(data) == 0:
            return pd.DataFrame()
        
        # This is a simplified landfall detection
        # In reality, you'd need coastline data for accurate detection
        
        landfall_points = []
        
        for (storm_name, year), storm_group in data.groupby(['name', 'year']):
            storm_group = storm_group.sort_values('datetime')
            
            # Look for points where storm enters Gulf Coast bounding box
            # This is a rough approximation
            gulf_points = storm_group[
                (storm_group['lat'] >= self.GULF_COAST_BOUNDS['lat_min']) &
                (storm_group['lat'] <= self.GULF_COAST_BOUNDS['lat_max']) &
                (storm_group['long'] >= self.GULF_COAST_BOUNDS['lon_min']) &
                (storm_group['long'] <= self.GULF_COAST_BOUNDS['lon_max'])
            ]
            
            if len(gulf_points) > 0:
                # Take the first point in Gulf Coast region as potential landfall
                landfall = gulf_points.iloc[0].copy()
                landfall_points.append(landfall)
        
        return pd.DataFrame(landfall_points) if landfall_points else pd.DataFrame()
    
    def get_storm_tracks(self, data: pd.DataFrame = None, limit: int = None) -> Dict:
        """Get individual storm track data for mapping"""
        if data is None:
            data = self.gulf_coast_data
        
        if data is None or len(data) == 0:
            return {}
        
        tracks = {}
        storm_groups = data.groupby(['name', 'year'])
        
        # If limit specified, take most recent storms
        if limit:
            storm_groups = list(storm_groups)[-limit:]
        
        for (storm_name, year), storm_data in storm_groups:
            storm_data = storm_data.sort_values('datetime')
            
            track_data = {
                'name': f"{storm_name} ({year})",
                'year': year,
                'lats': storm_data['lat'].tolist(),
                'lons': storm_data['long'].tolist(),
                'winds': storm_data['wind'].tolist(),
                'pressures': storm_data['pressure'].tolist(),
                'categories': storm_data['category'].tolist(),
                'datetimes': storm_data['datetime'].tolist(),
                'max_wind': storm_data['wind'].max(),
                'min_pressure': storm_data['pressure'].min(),
                'duration_hours': len(storm_data) * 6  # Approximate: 6 hours per data point
            }
            
            tracks[f"{storm_name}_{year}"] = track_data
        
        return tracks
    
    def get_impact_statistics(self, data: pd.DataFrame = None) -> Dict:
        """Calculate impact area and frequency statistics"""
        if data is None:
            data = self.gulf_coast_data
        
        if data is None or len(data) == 0:
            return {}
        
        # Create geographic grid for impact analysis
        lat_bins = np.linspace(self.GULF_COAST_BOUNDS['lat_min'], 
                               self.GULF_COAST_BOUNDS['lat_max'], 20)
        lon_bins = np.linspace(self.GULF_COAST_BOUNDS['lon_min'], 
                               self.GULF_COAST_BOUNDS['lon_max'], 20)
        
        # Count storm occurrences in each grid cell
        impact_grid = np.zeros((len(lat_bins)-1, len(lon_bins)-1))
        
        for i in range(len(lat_bins)-1):
            for j in range(len(lon_bins)-1):
                lat_mask = (data['lat'] >= lat_bins[i]) & (data['lat'] < lat_bins[i+1])
                lon_mask = (data['long'] >= lon_bins[j]) & (data['long'] < lon_bins[j+1])
                
                # Count unique storms in this grid cell
                storms_in_cell = data[lat_mask & lon_mask].groupby(['name', 'year']).size()
                impact_grid[i, j] = len(storms_in_cell)
        
        return {
            'impact_grid': impact_grid,
            'lat_bins': lat_bins,
            'lon_bins': lon_bins,
            'total_storms': data.groupby(['name', 'year']).size().count(),
            'avg_storms_per_year': data.groupby(['name', 'year']).size().count() / 
                                   (data['year'].max() - data['year'].min() + 1) if len(data) > 0 else 0
        }
    
    def get_data_summary(self) -> Dict:
        """Get overall data summary statistics"""
        if self.gulf_coast_data is None:
            return {}
        
        return {
            'total_records': len(self.gulf_coast_data),
            'year_range': (self.gulf_coast_data['year'].min(), self.gulf_coast_data['year'].max()),
            'unique_storms': self.gulf_coast_data.groupby(['name', 'year']).size().count(),
            'categories_present': sorted(self.gulf_coast_data['category'].dropna().unique()),
            'status_types': self.gulf_coast_data['status'].value_counts().to_dict(),
            'geographic_bounds': {
                'lat_min': self.gulf_coast_data['lat'].min(),
                'lat_max': self.gulf_coast_data['lat'].max(),
                'lon_min': self.gulf_coast_data['long'].min(),
                'lon_max': self.gulf_coast_data['long'].max()
            }
        }

# Utility functions for data processing
def categorize_wind_speed(wind_speed: float) -> str:
    """Categorize wind speed into Saffir-Simpson scale"""
    if pd.isna(wind_speed):
        return 'Unknown'
    elif wind_speed < 39:
        return 'Tropical Depression'
    elif wind_speed < 74:
        return 'Tropical Storm'
    elif wind_speed < 96:
        return 'Category 1 Hurricane'
    elif wind_speed < 111:
        return 'Category 2 Hurricane'
    elif wind_speed < 130:
        return 'Category 3 Hurricane'
    elif wind_speed < 157:
        return 'Category 4 Hurricane'
    else:
        return 'Category 5 Hurricane'

def get_month_name(month_num: int) -> str:
    """Convert month number to name"""
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    return month_names.get(month_num, 'Unknown')