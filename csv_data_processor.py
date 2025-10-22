"""
Simple CSV Data Processor for Hurricane Dashboard (Database Fallback).

This module provides a simple CSV-based data processing system that works
when PostgreSQL database is not available, ensuring the application can
run with just the CSV dataset.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

class SimpleCsvDataProcessor:
    """Simple CSV-based data processor for hurricane data (database fallback)."""
    
    def __init__(self, csv_path: str = "storms.csv"):
        """Initialize the CSV data processor."""
        self.logger = logging.getLogger(__name__)
        self.csv_path = csv_path
        self.data = None
        
        # Legacy compatibility properties
        self.gulf_coast_data = None
        self.full_atlantic_data = None
        
        # Load CSV data
        self._load_csv_data()
    
    def _load_csv_data(self):
        """Load hurricane data from CSV file."""
        try:
            if not Path(self.csv_path).exists():
                raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
            
            # Load the CSV data
            self.data = pd.read_csv(self.csv_path)
            
            # Convert date columns
            if 'iso_time' in self.data.columns:
                self.data['iso_time'] = pd.to_datetime(self.data['iso_time'])
                self.data['year'] = self.data['iso_time'].dt.year
            
            # Set legacy properties
            self.full_atlantic_data = self.data.copy()
            
            # Filter for Gulf Coast region (rough approximation)
            if 'lat' in self.data.columns and 'lon' in self.data.columns:
                gulf_mask = (
                    (self.data['lat'] >= 24.0) & (self.data['lat'] <= 31.0) &
                    (self.data['lon'] >= -98.0) & (self.data['lon'] <= -80.0)
                )
                self.gulf_coast_data = self.data[gulf_mask].copy()
            else:
                self.gulf_coast_data = self.data.copy()
            
            self.logger.info(f"Loaded {len(self.data)} records from CSV")
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV data: {e}")
            # Create empty dataframes
            self.data = pd.DataFrame()
            self.gulf_coast_data = pd.DataFrame()
            self.full_atlantic_data = pd.DataFrame()
    
    def get_storm_list(self, dataset: str = "gulf_coast") -> List[str]:
        """Get list of storm names."""
        try:
            data = self.gulf_coast_data if dataset == "gulf_coast" else self.full_atlantic_data
            if data is None or data.empty:
                return []
            
            if 'name' in data.columns:
                storms = data['name'].dropna().unique().tolist()
                return sorted(storms)
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting storm list: {e}")
            return []
    
    def get_storm_data(self, storm_name: str, dataset: str = "gulf_coast") -> pd.DataFrame:
        """Get data for a specific storm."""
        try:
            data = self.gulf_coast_data if dataset == "gulf_coast" else self.full_atlantic_data
            if data is None or data.empty:
                return pd.DataFrame()
            
            if 'name' in data.columns:
                storm_data = data[data['name'] == storm_name].copy()
                return storm_data
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting storm data: {e}")
            return pd.DataFrame()
    
    def get_dataset_for_analysis(self, dataset: str = "gulf_coast", 
                                year_range: Optional[Tuple[int, int]] = None) -> pd.DataFrame:
        """Get dataset for analysis with optional year filtering."""
        try:
            data = self.gulf_coast_data if dataset == "gulf_coast" else self.full_atlantic_data
            if data is None or data.empty:
                return pd.DataFrame()
            
            # Apply year filtering if specified
            if year_range and 'year' in data.columns:
                start_year, end_year = year_range
                data = data[(data['year'] >= start_year) & (data['year'] <= end_year)]
            
            return data.copy()
            
        except Exception as e:
            self.logger.error(f"Error getting dataset: {e}")
            return pd.DataFrame()
    
    def get_storms_by_year(self, year: int, dataset: str = "gulf_coast") -> List[str]:
        """Get storms for a specific year."""
        try:
            data = self.get_dataset_for_analysis(dataset, (year, year))
            if data.empty:
                return []
            
            if 'name' in data.columns:
                storms = data['name'].dropna().unique().tolist()
                return sorted(storms)
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting storms by year: {e}")
            return []
    
    def get_category_distribution(self, dataset: str = "gulf_coast") -> Dict[str, int]:
        """Get hurricane category distribution."""
        try:
            data = self.gulf_coast_data if dataset == "gulf_coast" else self.full_atlantic_data
            if data is None or data.empty:
                return {}
            
            # Try to determine category from wind speed
            if 'usa_wind' in data.columns:
                data = data.dropna(subset=['usa_wind'])
                
                def get_category(wind_speed):
                    if wind_speed < 39:
                        return "Tropical Depression"
                    elif wind_speed < 74:
                        return "Tropical Storm"
                    elif wind_speed < 96:
                        return "Category 1"
                    elif wind_speed < 111:
                        return "Category 2"
                    elif wind_speed < 130:
                        return "Category 3"
                    elif wind_speed < 157:
                        return "Category 4"
                    else:
                        return "Category 5"
                
                data['category'] = data['usa_wind'].apply(get_category)
                distribution = data['category'].value_counts().to_dict()
                return distribution
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting category distribution: {e}")
            return {}
    
    def prepare_full_atlantic_data(self):
        """Legacy method for compatibility."""
        return self.full_atlantic_data
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics."""
        try:
            summary = {
                'total_storms': 0,
                'total_records': 0,
                'year_range': (None, None),
                'categories': {},
                'last_updated': datetime.now().isoformat()
            }
            
            if self.data is not None and not self.data.empty:
                summary['total_records'] = len(self.data)
                
                if 'name' in self.data.columns:
                    summary['total_storms'] = self.data['name'].nunique()
                
                if 'year' in self.data.columns:
                    years = self.data['year'].dropna()
                    if not years.empty:
                        summary['year_range'] = (int(years.min()), int(years.max()))
                
                summary['categories'] = self.get_category_distribution("full_atlantic")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard summary: {e}")
            return {
                'total_storms': 0,
                'total_records': 0,
                'year_range': (None, None),
                'categories': {},
                'last_updated': datetime.now().isoformat()
            }

# Create a compatibility alias
HurricaneDataProcessor = SimpleCsvDataProcessor