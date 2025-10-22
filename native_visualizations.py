"""
Native GUI Visualizations for Hurricane Dashboard
High-performance matplotlib-based visualizations with native GUI integration and aesthetic theming
"""

import matplotlib
# Set matplotlib to use TkAgg backend for native GUI integration
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import seaborn as sns
from typing import List, Tuple, Optional, Dict, Any
import threading
from dataclasses import dataclass

# Import settings system
try:
    from settings_manager import VisualizationSettings
    from aesthetic_theme import get_theme, AestheticTheme
except ImportError:
    # Fallback if settings not available
    @dataclass
    class VisualizationSettings:
        figure_dpi: int = 100
        figure_style: str = 'dark_background'

# Configure matplotlib for better performance and appearance
def configure_matplotlib(settings: Optional[VisualizationSettings] = None, theme=None):
    """Configure matplotlib based on settings and theme"""
    if settings is None:
        settings = VisualizationSettings()
    
    plt.style.use(settings.figure_style)
    
    # Use theme colors if available
    chart_bg = theme.colors.chart_bg if theme else '#2b2b2b'
    matplotlib.rcParams['figure.facecolor'] = chart_bg
    matplotlib.rcParams['axes.facecolor'] = chart_bg
    matplotlib.rcParams['savefig.facecolor'] = chart_bg
    matplotlib.rcParams['font.size'] = 10
    matplotlib.rcParams['axes.titlesize'] = 12
    matplotlib.rcParams['axes.labelsize'] = 10
    matplotlib.rcParams['xtick.labelsize'] = 9
    matplotlib.rcParams['ytick.labelsize'] = 9
    matplotlib.rcParams['figure.dpi'] = settings.figure_dpi
    
    # Configure layout settings for optimal compatibility
    matplotlib.rcParams['figure.autolayout'] = False  # Disable automatic layout
    matplotlib.rcParams['figure.constrained_layout.use'] = False  # Use manual layout control
    
    # Set default layout to 'none' for manual control (compatible with all matplotlib versions)
    if hasattr(matplotlib, 'get_backend'):
        # Suppress layout-related warnings for better user experience  
        import warnings
        warnings.filterwarnings('ignore', message='This figure includes Axes that are not compatible with tight_layout')
        warnings.filterwarnings('ignore', message="The Figure parameters 'tight_layout' and 'constrained_layout' cannot be used together")
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.figure')

# Initial configuration
configure_matplotlib()

@dataclass
class PlotConfig:
    """Configuration for plot appearance and behavior"""
    width: int = 12
    height: int = 8
    dpi: int = 100
    title_color: str = '#ffffff'
    text_color: str = '#cccccc'
    grid_color: str = '#404040'
    highlight_color: str = '#ff6b35'
    primary_color: str = '#4a90e2'
    secondary_color: str = '#f5a623'

class NativeVisualizationEngine:
    """High-performance native GUI visualization engine using matplotlib"""
    
    def __init__(self, parent_widget=None, settings: Optional[VisualizationSettings] = None):
        """Initialize the visualization engine with aesthetic theming"""
        self.parent_widget = parent_widget
        self.settings = settings or VisualizationSettings()
        self.config = PlotConfig(dpi=self.settings.figure_dpi)
        
        # Initialize aesthetic theme
        try:
            self.theme = get_theme()
        except:
            # Fallback if theme not available
            self.theme = None
        
        # Configure matplotlib with current settings and theme
        configure_matplotlib(self.settings, self.theme)
        
        # Active figures and canvases
        self.active_figures: Dict[str, Figure] = {}
        self.active_canvases: Dict[str, FigureCanvasTkAgg] = {}
        self.active_toolbars: Dict[str, NavigationToolbar2Tk] = {}
        
        # Data caching for performance
        self.data_cache: Dict[str, Any] = {}
        self.plot_cache: Dict[str, Any] = {}
        
        # Selected storms for highlighting
        self.selected_storms: List[str] = []
        
        # Performance tracking
        self.render_times: Dict[str, float] = {}
        
        print("✅ Native visualization engine initialized with matplotlib TkAgg backend")
    
    def create_embedded_canvas(self, parent_frame, plot_type: str, 
                             width: int = None, height: int = None) -> Tuple[Figure, FigureCanvasTkAgg]:
        """Create an embedded matplotlib canvas widget in tkinter frame"""
        
        # Get actual available space from parent frame with retry for proper sizing
        parent_frame.update_idletasks()  # Ensure frame is rendered
        available_width = parent_frame.winfo_width()
        available_height = parent_frame.winfo_height()
        
        # If frame hasn't been sized yet, try to get dimensions from parent hierarchy
        if available_width <= 1 or available_height <= 1:
            # Try to get size from tab notebook or main window
            current_widget = parent_frame
            for _ in range(3):  # Check up to 3 levels up
                current_widget = current_widget.master
                if current_widget:
                    test_width = current_widget.winfo_width()
                    test_height = current_widget.winfo_height()
                    if test_width > 100 and test_height > 100:
                        # Use parent size with reasonable deduction for borders/tabs
                        available_width = test_width - 50  # Account for padding/borders
                        available_height = test_height - 150  # Account for tabs/headers
                        break
        
        # Final fallbacks based on plot type if still no good dimensions
        if available_width <= 1:
            available_width = 1400 if plot_type == "map" else 1200
        if available_height <= 1:  
            available_height = 800 if plot_type == "map" else 600
        
        # Use responsive sizing based on available space with appropriate margins
        if plot_type == "map":  # Map visualizations need to fit available space
            # Use most of available space but leave room for frame borders and scrollbars
            pixel_width = max(600, int(available_width * 0.92))   # 92% width, at least 600px 
            pixel_height = max(400, int(available_height * 0.82)) # 82% height, leave room for margins
        elif width and width > 1000:  # Large tab interface
            pixel_width = max(700, int(available_width * 0.90))
            pixel_height = max(500, int(available_height * 0.80))
        else:  # Regular embedded view
            pixel_width = max(500, int(available_width * 0.85))
            pixel_height = max(350, int(available_height * 0.75))
        
        # Convert pixels to inches using DPI
        fig_width = pixel_width / self.config.dpi
        fig_height = pixel_height / self.config.dpi
        
        # Create figure with manual layout and themed styling
        facecolor = self.theme.colors.chart_bg if self.theme else '#2b2b2b'
        fig = Figure(figsize=(fig_width, fig_height), 
                    dpi=self.config.dpi,
                    facecolor=facecolor,
                    layout='none')  # Use explicit 'none' layout for full manual control
        
        # Set optimized margins based on plot type with manual layout control
        if plot_type == "map":
            # Optimized layout for geographic visualizations - balanced margins for proper aspect ratio
            # Leave more room for axis labels while maintaining good proportions
            fig.subplots_adjust(left=0.08, bottom=0.12, right=0.96, top=0.88, wspace=0.1, hspace=0.1)
        else:
            # Standard margins for timeline and analysis visualizations
            fig.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.9, wspace=0.2, hspace=0.3)
        
        # Create canvas widget - use grid to match parent frame management
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        
        # Configure parent frame grid if needed
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        
        # Use grid instead of pack to avoid geometry manager conflicts
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        
        # Skip navigation toolbar to avoid geometry manager conflicts
        # The toolbar uses pack() internally which conflicts with our grid layout
        toolbar = None
        
        # Enable interactive features through canvas events instead
        def on_scroll(event):
            """Handle mouse wheel scrolling for zoom"""
            if event.inaxes:
                scale_factor = 1.1 if event.button == 'up' else 0.9
                xlim = event.inaxes.get_xlim()
                ylim = event.inaxes.get_ylim()
                event.inaxes.set_xlim([x * scale_factor for x in xlim])
                event.inaxes.set_ylim([y * scale_factor for y in ylim])
                canvas.draw_idle()
        
        # Connect scroll event for basic interactivity
        canvas.mpl_connect('scroll_event', on_scroll)
        
        return fig, canvas
    
    def _apply_theme_to_axes(self, ax, apply_grid: bool = True):
        """Apply theme styling to matplotlib axes"""
        if self.theme:
            # Use theme's apply_chart_styling method
            # Note: We need to get the figure from the axes
            fig = ax.get_figure()
            self.theme.apply_chart_styling(fig, ax)
        else:
            # Fallback styling for when no theme is available
            ax.set_facecolor('#2b2b2b')
            if apply_grid:
                ax.grid(True, alpha=0.3, color='gray')
    
    def _apply_map_filters(self, data: pd.DataFrame, filter_options: Dict) -> pd.DataFrame:
        """Apply filtering options to storm data for map visualization"""
        filtered_data = data.copy()
        
        # Year range filtering
        if 'year_start' in filter_options and 'year_end' in filter_options:
            filtered_data = filtered_data[
                (filtered_data['year'] >= filter_options['year_start']) &
                (filtered_data['year'] <= filter_options['year_end'])
            ]
        
        # Category filtering
        if 'categories' in filter_options and filter_options['categories']:
            # Filter by hurricane categories
            filtered_data = filtered_data[
                filtered_data['category'].isin(filter_options['categories'])
            ]
        
        # Wind speed filtering
        if 'min_wind' in filter_options:
            filtered_data = filtered_data[filtered_data['wind'] >= filter_options['min_wind']]
        if 'max_wind' in filter_options:
            filtered_data = filtered_data[filtered_data['wind'] <= filter_options['max_wind']]
        
        # Season filtering (months)
        if 'months' in filter_options and filter_options['months']:
            filtered_data = filtered_data[filtered_data['month'].isin(filter_options['months'])]
        
        # Storm name filtering (partial match)
        if 'name_contains' in filter_options and filter_options['name_contains']:
            filtered_data = filtered_data[
                filtered_data['name'].str.contains(filter_options['name_contains'], case=False, na=False)
            ]
        
        return filtered_data
    
    def _create_regional_map_with_tracks(self, ax, data: pd.DataFrame, 
                                       selected_storms: List[str] = None,
                                       show_multiple_tracks: bool = True):
        """Create regional Gulf Coast map with multiple storm tracks"""
        
        # Define Gulf Coast region boundaries (expanded for better context)
        gulf_bounds = {
            'lat_min': 18.0,   # Include Caribbean for storm origins
            'lat_max': 35.0,   # Include inland tracking
            'lon_min': -105.0, # Include Texas and Mexico
            'lon_max': -75.0   # Include Florida and Atlantic
        }
        
        # Set map boundaries
        ax.set_xlim(gulf_bounds['lon_min'], gulf_bounds['lon_max'])
        ax.set_ylim(gulf_bounds['lat_min'], gulf_bounds['lat_max'])
        
        # Add coastline and geographic features
        self._add_coastline_features(ax, gulf_bounds)
        
        # Plot storm tracks
        if show_multiple_tracks:
            self._plot_multiple_storm_tracks(ax, data, selected_storms)
        else:
            # Plot single storm if specified
            if selected_storms and len(selected_storms) == 1:
                single_storm_data = data[data['name'] == selected_storms[0]]
                if not single_storm_data.empty:
                    self._plot_single_storm_track(ax, single_storm_data, highlighted=True)
        
        # Add map labels and styling
        self._style_regional_map(ax, gulf_bounds)
        
        # Add legend and annotations
        self._add_map_legend(ax, data)
    
    def _add_coastline_features(self, ax, bounds: Dict):
        """Add coastline and geographic features to the map"""
        
        # Create a simple coastline representation
        # Gulf Coast states outline (simplified coordinates)
        
        # Texas coast
        texas_coast_lon = [-97.5, -96.8, -95.5, -94.0, -93.8]
        texas_coast_lat = [25.8, 27.8, 29.3, 29.8, 29.7]
        
        # Louisiana coast
        louisiana_coast_lon = [-93.8, -92.2, -91.0, -89.2, -89.0]
        louisiana_coast_lat = [29.7, 29.8, 29.5, 29.2, 29.0]
        
        # Mississippi/Alabama coast
        ms_al_coast_lon = [-89.0, -88.0, -87.5, -87.0]
        ms_al_coast_lat = [29.0, 30.2, 30.3, 30.4]
        
        # Florida coast (Gulf side)
        florida_coast_lon = [-87.0, -86.5, -85.0, -83.0, -82.5, -81.8]
        florida_coast_lat = [30.4, 30.2, 29.8, 28.5, 27.8, 26.5]
        
        # Plot coastlines
        ax.plot(texas_coast_lon, texas_coast_lat, 'k-', linewidth=2, alpha=0.8, label='Coastline')
        ax.plot(louisiana_coast_lon, louisiana_coast_lat, 'k-', linewidth=2, alpha=0.8)
        ax.plot(ms_al_coast_lon, ms_al_coast_lat, 'k-', linewidth=2, alpha=0.8)
        ax.plot(florida_coast_lon, florida_coast_lat, 'k-', linewidth=2, alpha=0.8)
        
        # Add state labels
        ax.text(-100.0, 31.0, 'TEXAS', fontsize=10, fontweight='bold', alpha=0.7)
        ax.text(-92.0, 31.5, 'LOUISIANA', fontsize=10, fontweight='bold', alpha=0.7)
        ax.text(-88.5, 32.0, 'MISSISSIPPI', fontsize=9, fontweight='bold', alpha=0.7)
        ax.text(-86.0, 32.5, 'ALABAMA', fontsize=9, fontweight='bold', alpha=0.7)
        ax.text(-84.0, 28.0, 'FLORIDA', fontsize=10, fontweight='bold', alpha=0.7)
        
        # Add Gulf of Mexico label
        ax.text(-92.0, 26.0, 'GULF OF MEXICO', fontsize=12, fontweight='bold', 
                alpha=0.5, ha='center')
        
        # Add major cities
        cities = {
            'Houston': (-95.37, 29.76),
            'New Orleans': (-90.07, 29.95),
            'Mobile': (-88.04, 30.69),
            'Tampa': (-82.46, 27.95),
            'Miami': (-80.19, 25.76)
        }
        
        for city, (lon, lat) in cities.items():
            if bounds['lon_min'] <= lon <= bounds['lon_max'] and bounds['lat_min'] <= lat <= bounds['lat_max']:
                ax.plot(lon, lat, 'ko', markersize=4)
                ax.text(lon, lat + 0.3, city, fontsize=8, ha='center', alpha=0.8)
    
    def _plot_multiple_storm_tracks(self, ax, data: pd.DataFrame, selected_storms: List[str] = None):
        """Plot multiple storm tracks on the regional map"""
        
        # Group data by storm (name + year)
        storm_groups = data.groupby(['name', 'year'])
        
        # Color schemes for different categories
        category_colors = {
            'Tropical Depression': '#74a9cf',
            'Tropical Storm': '#2b8cbe', 
            'Category 1': '#fdae6b',
            'Category 2': '#fd8d3c',
            'Category 3': '#e6550d',
            'Category 4': '#bd0026',
            'Category 5': '#7f0000',
            'Unknown': '#969696'
        }
        
        track_count = 0
        highlighted_tracks = []
        
        for (storm_name, year), storm_group in storm_groups:
            storm_identifier = f"{storm_name} ({year})"
            
            # Skip if we have too many tracks (performance consideration)
            if track_count > 50 and storm_identifier not in (selected_storms or []):
                continue
                
            # Determine if this storm should be highlighted
            is_highlighted = selected_storms and storm_identifier in selected_storms
            
            # Sort by time progression
            storm_track = storm_group.sort_values(['month', 'day', 'hour'])
            
            if len(storm_track) < 2:  # Need at least 2 points for a track
                continue
            
            # Get coordinates
            lons = storm_track['long'].values
            lats = storm_track['lat'].values
            
            # Determine track color based on maximum category
            max_category = self._get_storm_max_category(storm_track)
            track_color = category_colors.get(max_category, category_colors['Unknown'])
            
            # Set track properties
            if is_highlighted:
                linewidth = 3.0
                alpha = 1.0
                zorder = 10
                highlighted_tracks.append(storm_identifier)
            else:
                linewidth = 1.5
                alpha = 0.6
                zorder = 5
            
            # Plot the track
            ax.plot(lons, lats, color=track_color, linewidth=linewidth, 
                   alpha=alpha, zorder=zorder, label=storm_identifier if is_highlighted else "")
            
            # Add start/end markers
            if is_highlighted or track_count < 10:  # Only show markers for highlighted or first few storms
                # Start marker (green circle)
                ax.plot(lons[0], lats[0], 'go', markersize=6, zorder=zorder+1, 
                       markeredgecolor='white', markeredgewidth=1)
                
                # End marker (red square)
                ax.plot(lons[-1], lats[-1], 'rs', markersize=6, zorder=zorder+1,
                       markeredgecolor='white', markeredgewidth=1)
                
                # Add storm label for highlighted storms
                if is_highlighted:
                    ax.text(lons[len(lons)//2], lats[len(lats)//2], 
                           f"{storm_name}\n{year}", fontsize=9, fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", 
                                    facecolor=self.theme.colors.surface if self.theme else 'white', 
                                    alpha=0.8),
                           ha='center', va='center', zorder=15)
            
            track_count += 1
        
        print(f"📍 Plotted {track_count} storm tracks on regional map")
        if highlighted_tracks:
            print(f"🌟 Highlighted storms: {', '.join(highlighted_tracks)}")
    
    def _plot_single_storm_track(self, ax, storm_data: pd.DataFrame, highlighted: bool = True):
        """Plot a single storm track with detailed progression markers"""
        
        # Sort by time progression
        storm_track = storm_data.sort_values(['month', 'day', 'hour'])
        
        if len(storm_track) < 2:
            return
        
        # Get coordinates and intensities
        lons = storm_track['long'].values
        lats = storm_track['lat'].values
        winds = storm_track['wind'].values
        
        # Create color-coded track based on wind intensity
        from matplotlib.collections import LineCollection
        import matplotlib.colors as mcolors
        
        # Create line segments
        points = np.array([lons, lats]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # Create color map for wind speeds
        norm = mcolors.Normalize(vmin=winds.min(), vmax=winds.max())
        cmap = plt.cm.get_cmap('plasma')
        
        # Create line collection
        lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=4, alpha=0.8)
        lc.set_array(winds[:-1])  # Use wind speeds to color segments
        ax.add_collection(lc)
        
        # Add colorbar for wind speeds
        cbar = plt.colorbar(lc, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('Wind Speed (mph)', rotation=270, labelpad=15)
        
        # Add detailed markers for significant points
        for i, (lon, lat, wind) in enumerate(zip(lons[::6], lats[::6], winds[::6])):  # Every 6th point
            marker_size = max(4, min(12, wind / 10))  # Scale marker with wind speed
            ax.plot(lon, lat, 'o', color='white', markersize=marker_size+2, zorder=10)
            ax.plot(lon, lat, 'o', color='red', markersize=marker_size, zorder=11)
    
    def _get_storm_max_category(self, storm_data: pd.DataFrame) -> str:
        """Determine the maximum category reached by a storm"""
        
        # Check if category column exists and has valid data
        if 'category' in storm_data.columns:
            categories = storm_data['category'].dropna()
            if not categories.empty:
                # Find the highest numeric category
                numeric_categories = []
                for cat in categories:
                    if isinstance(cat, (int, float)) and not pd.isna(cat):
                        numeric_categories.append(int(cat))
                
                if numeric_categories:
                    max_cat = max(numeric_categories)
                    return f"Category {max_cat}"
        
        # Fallback: use wind speed to estimate category
        max_wind = storm_data['wind'].max()
        if pd.isna(max_wind):
            return 'Unknown'
        
        if max_wind < 39:
            return 'Tropical Depression'
        elif max_wind < 74:
            return 'Tropical Storm'
        elif max_wind < 96:
            return 'Category 1'
        elif max_wind < 111:
            return 'Category 2' 
        elif max_wind < 129:
            return 'Category 3'
        elif max_wind < 157:
            return 'Category 4'
        else:
            return 'Category 5'
    
    def _style_regional_map(self, ax, bounds: Dict):
        """Apply styling to the regional map"""
        
        # Set labels
        ax.set_xlabel('Longitude (°W)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
        ax.set_title('Gulf Coast Hurricane Tracks - Regional Analysis', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Format longitude labels to show as positive (West)
        lon_ticks = ax.get_xticks()
        ax.set_xticklabels([f'{abs(lon):.0f}°W' for lon in lon_ticks])
        
        # Format latitude labels
        lat_ticks = ax.get_yticks()  
        ax.set_yticklabels([f'{lat:.0f}°N' for lat in lat_ticks])
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Set aspect ratio to maintain geographic proportions
        ax.set_aspect('equal', adjustable='box')
        
        # Style the plot area
        ocean_color = '#f0f8ff'  # Default ocean color
        if self.theme:
            ocean_color = self.theme.colors.map_ocean_bg if hasattr(self.theme.colors, 'map_ocean_bg') else '#f0f8ff'
        ax.set_facecolor(ocean_color)
    
    def _add_map_legend(self, ax, data: pd.DataFrame):
        """Add legend and information to the map"""
        
        # Create legend elements
        legend_elements = []
        
        # Storm track legend
        legend_elements.append(plt.Line2D([0], [0], color='red', linewidth=3, 
                                        label='Highlighted Storm'))
        legend_elements.append(plt.Line2D([0], [0], color='blue', linewidth=2, alpha=0.6,
                                        label='Other Storm Tracks'))
        
        # Marker legend
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='green', 
                                        linestyle='None', markersize=6,
                                        label='Storm Origin'))
        legend_elements.append(plt.Line2D([0], [0], marker='s', color='red',
                                        linestyle='None', markersize=6, 
                                        label='Storm Terminus'))
        
        # Add legend
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98),
                 fancybox=True, shadow=True, fontsize=10)
        
        # Add summary statistics
        total_storms = len(data.groupby(['name', 'year']))
        date_range = f"{data['year'].min()}-{data['year'].max()}"
        
        info_text = f"Total Storms: {total_storms}\nPeriod: {date_range}\nRegion: Gulf Coast"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
               facecolor='white', alpha=0.8))
        
        # Store references
        self.active_figures[plot_type] = fig
        self.active_canvases[plot_type] = canvas
        self.active_toolbars[plot_type] = toolbar
        
        # Configure canvas for performance
        canvas.mpl_connect('draw_event', self._on_canvas_draw)
        
        return fig, canvas
    
    def generate_timeline_visualization(self, data: pd.DataFrame, 
                                      parent_frame, selected_storms: List[str] = None) -> Dict[str, Any]:
        """Generate enhanced timeline visualization with 4 data stories using different chart types"""
        import time
        start_time = time.time()
        
        if data.empty:
            return self._create_empty_plot(parent_frame, "timeline", "No data available for timeline")
        
        # Create embedded canvas with larger size for multi-panel layout
        fig, canvas = self.create_embedded_canvas(parent_frame, "timeline")
        
        # Clear any existing plots
        fig.clear()
        
        # Create 2x2 subplot grid for 4 different data stories
        gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25, 
                             left=0.08, right=0.95, top=0.93, bottom=0.08)
        
        # Story 1: Annual Storm Activity Timeline (Top Left) - Line Chart
        ax1 = fig.add_subplot(gs[0, 0])
        self._apply_theme_to_axes(ax1, apply_grid=True)
        self._create_annual_activity_story(ax1, data, selected_storms)
        
        # Story 2: Seasonal Distribution Pattern (Top Right) - Polar/Circular Chart
        ax2 = fig.add_subplot(gs[0, 1])
        self._apply_theme_to_axes(ax2, apply_grid=False)
        self._create_seasonal_pattern_story(ax2, data)
        
        # Story 3: Intensity Evolution Over Time (Bottom Left) - Area Chart
        ax3 = fig.add_subplot(gs[1, 0])
        self._apply_theme_to_axes(ax3, apply_grid=True)
        self._create_intensity_evolution_story(ax3, data)
        
        # Story 4: Hurricane Category Distribution by Decade (Bottom Right) - Stacked Bar Chart
        ax4 = fig.add_subplot(gs[1, 1])
        self._apply_theme_to_axes(ax4, apply_grid=True)
        self._create_decadal_category_story(ax4, data)
        
        # Add overall title
        fig.suptitle('Hurricane Timeline Analysis - Four Data Stories', 
                    fontsize=16, fontweight='bold', 
                    color=self.config.title_color if hasattr(self.config, 'title_color') else '#ffffff')
        
        # Update canvas
        canvas.draw_idle()
        
        # Performance tracking
        render_time = time.time() - start_time
        self.render_times['timeline'] = render_time
        
        return {
            'figure': fig,
            'canvas': canvas,
            'data_summary': {
                'total_years': len(data['year'].unique()) if not data.empty else 0,
                'total_storms': len(data.groupby(['name', 'year'])) if not data.empty else 0,
                'render_time_ms': render_time * 1000,
                'stories': ['Annual Activity', 'Seasonal Patterns', 'Intensity Evolution', 'Decadal Categories']
            }
        }
    
    def _create_annual_activity_story(self, ax, data: pd.DataFrame, selected_storms: List[str] = None):
        """Story 1: Annual Storm Activity Timeline - Line Chart with trend analysis"""
        # Process data for timeline
        yearly_data = self._process_timeline_data(data)
        
        years = yearly_data['year'].values
        counts = yearly_data['storm_count'].values
        
        if len(years) == 0:
            ax.text(0.5, 0.5, 'No temporal data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Main timeline with enhanced styling
        line = ax.plot(years, counts, 
                      color='#4a90e2',
                      linewidth=3,
                      marker='o',
                      markersize=5,
                      alpha=0.9,
                      label='Annual Storm Count',
                      markerfacecolor='white',
                      markeredgecolor='#4a90e2',
                      markeredgewidth=2)[0]
        
        # Add trend line with confidence interval
        if len(years) > 3:
            z = np.polyfit(years, counts, 1)
            trend_line = np.poly1d(z)
            trend_values = trend_line(years)
            
            ax.plot(years, trend_values, 
                   color='#ff6b35',
                   linestyle='--',
                   linewidth=2.5,
                   alpha=0.8,
                   label=f'Trend ({"↗" if z[0] > 0 else "↘"})')
            
            # Add confidence band
            residuals = counts - trend_values
            std_dev = np.std(residuals)
            ax.fill_between(years, trend_values - std_dev, trend_values + std_dev,
                           color='#ff6b35', alpha=0.2, label='Trend Range')
        
        # Highlight notable years (high activity)
        if len(counts) > 5:
            high_activity_threshold = np.percentile(counts, 90)
            high_activity_years = years[counts >= high_activity_threshold]
            high_activity_counts = counts[counts >= high_activity_threshold]
            
            ax.scatter(high_activity_years, high_activity_counts, 
                      color='#ff4757', s=80, alpha=0.8, 
                      marker='*', zorder=10, label='High Activity Years')
        
        # Styling
        ax.set_xlabel('Year', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of Storms', fontsize=11, fontweight='bold')
        ax.set_title('📈 Annual Hurricane Activity Timeline', fontsize=13, fontweight='bold', pad=15)
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle=':')
        
        # Add statistics annotation
        avg_storms = np.mean(counts)
        max_year = years[np.argmax(counts)]
        max_count = np.max(counts)
        
        stats_text = f'Average: {avg_storms:.1f} storms/year\nPeak: {max_count} storms ({max_year})'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', fontsize=10,
               bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7))
    
    def _create_seasonal_pattern_story(self, ax, data: pd.DataFrame):
        """Story 2: Seasonal Distribution Pattern - Circular/Polar Chart"""
        # Calculate monthly storm frequency
        if 'month' not in data.columns:
            ax.text(0.5, 0.5, 'No monthly data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        monthly_counts = data.groupby('month').size()
        
        # Ensure all months are represented
        all_months = pd.Series(index=range(1, 13), data=0)
        all_months.update(monthly_counts)
        monthly_counts = all_months.fillna(0)
        
        months = monthly_counts.index.values
        counts = monthly_counts.values
        
        # Create enhanced circular bar chart
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Color gradient for hurricane season intensity
        colors = ['#74a9cf' if i < 6 or i > 10 else '#e34a33' if 7 <= i <= 9 else '#fd8d3c' 
                 for i in range(1, 13)]
        
        bars = ax.bar(months, counts, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Highlight peak season
        peak_season_months = [6, 7, 8, 9, 10, 11]  # June-November
        for i, bar in enumerate(bars):
            if (i + 1) in peak_season_months:
                bar.set_edgecolor('#ff4757')
                bar.set_linewidth(2)
        
        # Styling
        ax.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax.set_ylabel('Storm Count', fontsize=11, fontweight='bold') 
        ax.set_title('🌀 Seasonal Hurricane Pattern', fontsize=13, fontweight='bold', pad=15)
        ax.set_xticks(months)
        ax.set_xticklabels(month_names, rotation=45)
        
        # Add season annotations
        peak_months = months[6:11]  # July-November (peak season)
        if len(peak_months) > 0:
            peak_avg = np.mean([counts[i-1] for i in peak_months if i-1 < len(counts)])
            off_season_avg = np.mean([counts[i-1] for i in months if i not in peak_months and i-1 < len(counts)])
            
            ax.axhspan(0, peak_avg, alpha=0.2, color='red', 
                      label=f'Peak Season Avg: {peak_avg:.1f}')
            
            # Add text annotation
            season_text = f'Peak Season (Jun-Nov)\nAverage: {peak_avg:.1f} storms'
            ax.text(0.98, 0.98, season_text, transform=ax.transAxes,
                   verticalalignment='top', horizontalalignment='right', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='red', alpha=0.7))
    
    def _create_intensity_evolution_story(self, ax, data: pd.DataFrame):
        """Story 3: Intensity Evolution Over Time - Area Chart showing wind speed trends"""
        # Calculate yearly average wind speeds by category
        if 'wind' not in data.columns:
            ax.text(0.5, 0.5, 'No wind speed data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Group by year and calculate intensity metrics
        yearly_intensity = data.groupby('year').agg({
            'wind': ['mean', 'max', 'min', 'std']
        }).round(1)
        
        yearly_intensity.columns = ['avg_wind', 'max_wind', 'min_wind', 'std_wind']
        yearly_intensity = yearly_intensity.dropna()
        
        if yearly_intensity.empty:
            ax.text(0.5, 0.5, 'Insufficient intensity data', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        years = yearly_intensity.index.values
        avg_winds = yearly_intensity['avg_wind'].values
        max_winds = yearly_intensity['max_wind'].values
        min_winds = yearly_intensity['min_wind'].values
        std_winds = yearly_intensity['std_wind'].fillna(0).values
        
        # Create layered area chart
        ax.fill_between(years, min_winds, max_winds, 
                       color='#74a9cf', alpha=0.3, label='Wind Speed Range')
        
        ax.fill_between(years, avg_winds - std_winds, avg_winds + std_winds,
                       color='#fd8d3c', alpha=0.5, label='Average ± Std Dev')
        
        ax.plot(years, avg_winds, color='#2b8cbe', linewidth=3, 
               marker='o', markersize=4, label='Average Wind Speed')
        
        ax.plot(years, max_winds, color='#e34a33', linewidth=2, 
               linestyle='--', alpha=0.8, label='Peak Wind Speed')
        
        # Add category thresholds
        category_thresholds = [74, 96, 111, 130, 157]
        category_names = ['Cat 1', 'Cat 2', 'Cat 3', 'Cat 4', 'Cat 5']
        colors = ['#fdcc8a', '#fc8d59', '#e34a33', '#b30000', '#7a0177']
        
        for i, (threshold, name, color) in enumerate(zip(category_thresholds, category_names, colors)):
            if threshold <= max(max_winds):
                ax.axhline(y=threshold, color=color, linestyle=':', alpha=0.7, linewidth=1)
                ax.text(max(years), threshold, f' {name}', verticalalignment='bottom', fontsize=9)
        
        # Styling
        ax.set_xlabel('Year', fontsize=11, fontweight='bold')
        ax.set_ylabel('Wind Speed (mph)', fontsize=11, fontweight='bold')
        ax.set_title('💨 Hurricane Intensity Evolution', fontsize=13, fontweight='bold', pad=15)
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle=':')
        
        # Add trend analysis
        if len(avg_winds) > 3:
            z = np.polyfit(years, avg_winds, 1)
            trend_direction = "strengthening" if z[0] > 0 else "weakening"
            trend_text = f'Intensity Trend: {trend_direction}\n({z[0]:+.2f} mph/year)'
            
            ax.text(0.02, 0.98, trend_text, transform=ax.transAxes,
                   verticalalignment='top', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', 
                            facecolor='green' if z[0] < 0 else 'red', alpha=0.7))
    
    def _create_decadal_category_story(self, ax, data: pd.DataFrame):
        """Story 4: Hurricane Category Distribution by Decade - Stacked Bar Chart"""
        # Calculate category distribution by decade
        if 'category' not in data.columns and 'wind' not in data.columns:
            ax.text(0.5, 0.5, 'No category data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Create decade groups
        data_copy = data.copy()
        data_copy['decade'] = (data_copy['year'] // 10) * 10
        
        # Determine categories from wind speed if category not available
        if 'category' not in data_copy.columns:
            data_copy['category'] = pd.cut(data_copy['wind'], 
                                         bins=[0, 39, 73, 95, 110, 129, 156, 999],
                                         labels=['TD', 'TS', '1', '2', '3', '4', '5'])
        
        # Group by decade and category
        decade_categories = data_copy.groupby(['decade', 'category']).size().unstack(fill_value=0)
        
        if decade_categories.empty:
            ax.text(0.5, 0.5, 'Insufficient category data', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Prepare data for stacked bar chart
        decades = decade_categories.index.values
        category_columns = ['TD', 'TS', '1', '2', '3', '4', '5']
        
        # Ensure all categories exist
        for cat in category_columns:
            if cat not in decade_categories.columns:
                decade_categories[cat] = 0
        
        # Colors for different categories
        colors = {
            'TD': '#74a9cf',   # Light blue
            'TS': '#2b8cbe',   # Blue  
            '1': '#fdcc8a',    # Light orange
            '2': '#fc8d59',    # Orange
            '3': '#e34a33',    # Red
            '4': '#b30000',    # Dark red
            '5': '#7a0177'     # Purple
        }
        
        # Create stacked bar chart
        bottom = np.zeros(len(decades))
        bar_width = 5  # 5-year width for decades
        
        for cat in category_columns:
            if cat in decade_categories.columns:
                values = decade_categories[cat].values
                bars = ax.bar(decades, values, bar_width, bottom=bottom, 
                             color=colors[cat], alpha=0.8, 
                             label=f'{"Tropical Depression" if cat == "TD" else "Tropical Storm" if cat == "TS" else f"Category {cat}"}',
                             edgecolor='white', linewidth=0.5)
                bottom += values
        
        # Styling
        ax.set_xlabel('Decade', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of Storms', fontsize=11, fontweight='bold')
        ax.set_title('📊 Hurricane Categories by Decade', fontsize=13, fontweight='bold', pad=15)
        
        # Format x-axis
        decade_labels = [f"{int(d)}s" for d in decades]
        ax.set_xticks(decades)
        ax.set_xticklabels(decade_labels, rotation=45)
        
        # Legend
        ax.legend(loc='upper right', fontsize=8, ncol=2)
        ax.grid(True, alpha=0.3, linestyle=':', axis='y')
        
        # Add trend annotation
        total_by_decade = decade_categories.sum(axis=1)
        if len(total_by_decade) > 2:
            recent_avg = total_by_decade.tail(2).mean()
            early_avg = total_by_decade.head(2).mean()
            change_pct = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
            
            trend_text = f'Activity Change:\n{change_pct:+.1f}% (recent vs early)'
            ax.text(0.02, 0.98, trend_text, transform=ax.transAxes,
                   verticalalignment='top', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', 
                            facecolor='green' if change_pct < 0 else 'orange', alpha=0.7))
    
    def generate_map_visualization(self, data: pd.DataFrame, 
                                 parent_frame, selected_storms: List[str] = None,
                                 show_multiple_tracks: bool = True,
                                 filter_options: Dict = None) -> Dict[str, Any]:
        """Generate enhanced regional map visualization with multiple storm tracks"""
        import time
        start_time = time.time()
        
        if data.empty:
            return self._create_empty_plot(parent_frame, "map", "No data available for map")
        
        # Create embedded canvas with larger size for regional mapping
        fig, canvas = self.create_embedded_canvas(parent_frame, "map")
        
        # Clear any existing plots
        fig.clear()
        
        # Create subplot for regional map
        ax = fig.add_subplot(111)
        
        # Apply theme styling to axes
        self._apply_theme_to_axes(ax, apply_grid=False)  # Maps don't need grid
        
        # Apply filtering options if provided
        filtered_data = self._apply_map_filters(data, filter_options or {})
        
        # Generate regional map with storm tracks
        if show_multiple_tracks and len(filtered_data) > 0:
            # Show multiple storm tracks for regional overview
            track_data = self._process_regional_tracks(filtered_data, selected_storms)
            self._plot_multiple_storm_tracks(ax, track_data, selected_storms)
        else:
            # Show single storm track
            track_data = self._process_single_track(filtered_data, selected_storms)
            self._plot_single_storm_track(ax, track_data, selected_storms)
        
        # Add Gulf Coast regional map features
        self._add_gulf_coast_features(ax)
        
        # Set regional map boundaries (Gulf Coast focus)
        self._set_regional_boundaries(ax, filtered_data)
        
        # Add map legend and labels
        self._add_map_legend_and_labels(ax, filtered_data)
        
        # Styling and formatting for Linux Mint compatibility
        self._style_regional_map(ax, filtered_data)
        
        # Add interactive features (Linux Mint optimized)
        self._add_regional_interactivity(ax, canvas, track_data)
        
        # Update canvas
        canvas.draw_idle()
        
        # Performance tracking
        render_time = time.time() - start_time
        self.render_times['map'] = render_time

        return {
            'figure': fig,
            'canvas': canvas,
            'data_summary': {
                'total_storms': len(filtered_data.groupby(['name', 'year'])) if not filtered_data.empty else 0,
                'total_tracks': len(track_data) if 'track_data' in locals() else 0,
                'render_time_ms': render_time * 1000,
                'map_type': 'regional_multi_track' if show_multiple_tracks else 'single_track'
            }
        }
    
    def _apply_map_filters(self, data: pd.DataFrame, filter_options: Dict) -> pd.DataFrame:
        """Apply filtering options to map data"""
        filtered_data = data.copy()
        
        # Year range filter
        if 'start_year' in filter_options and 'end_year' in filter_options:
            filtered_data = filtered_data[
                (filtered_data['year'] >= filter_options['start_year']) &
                (filtered_data['year'] <= filter_options['end_year'])
            ]
        
        # Category filter
        if 'categories' in filter_options and filter_options['categories']:
            # Handle both numeric and string categories
            category_mask = pd.Series(False, index=filtered_data.index)
            for cat in filter_options['categories']:
                if cat == 'TD':  # Tropical Depression
                    category_mask |= (filtered_data['status'] == 'tropical depression')
                elif cat == 'TS':  # Tropical Storm
                    category_mask |= (filtered_data['status'] == 'tropical storm')
                elif cat in ['1', '2', '3', '4', '5']:  # Hurricane categories
                    category_mask |= (filtered_data['category'] == int(cat))
            filtered_data = filtered_data[category_mask]
        
        # Wind speed filter
        if 'min_wind' in filter_options:
            filtered_data = filtered_data[filtered_data['wind'] >= filter_options['min_wind']]
        if 'max_wind' in filter_options:
            filtered_data = filtered_data[filtered_data['wind'] <= filter_options['max_wind']]
        
        # Month filter
        if 'months' in filter_options and filter_options['months']:
            filtered_data = filtered_data[filtered_data['month'].isin(filter_options['months'])]
        
        return filtered_data
    
    def _process_regional_tracks(self, data: pd.DataFrame, selected_storms: List[str] = None) -> Dict:
        """Process data for regional multi-track display"""
        track_data = {}
        
        # Group by storm (name + year combination)
        storm_groups = data.groupby(['name', 'year'])
        
        for (storm_name, year), storm_data in storm_groups:
            storm_key = f"{storm_name}_{year}"
            
            # Get track coordinates
            lats = storm_data['lat'].values
            lons = storm_data['long'].values
            
            # Get intensity data for color coding
            winds = storm_data['wind'].values
            categories = storm_data['category'].fillna(0).values
            
            # Determine if this storm is selected
            is_selected = selected_storms and f"{storm_name} ({year})" in selected_storms
            
            track_data[storm_key] = {
                'name': f"{storm_name} ({year})",
                'lats': lats,
                'lons': lons,
                'winds': winds,
                'categories': categories,
                'is_selected': is_selected,
                'max_wind': winds.max() if len(winds) > 0 else 0,
                'start_pos': (lons[0], lats[0]) if len(lons) > 0 else None,
                'end_pos': (lons[-1], lats[-1]) if len(lons) > 0 else None
            }
        
        return track_data
    
    def _process_single_track(self, data: pd.DataFrame, selected_storms: List[str] = None) -> Dict:
        """Process data for single storm track display"""
        if selected_storms and len(selected_storms) > 0:
            # Parse selected storm name
            storm_info = selected_storms[0]
            if '(' in storm_info and ')' in storm_info:
                storm_name = storm_info.split(' (')[0]
                year = int(storm_info.split(' (')[1].replace(')', ''))
                
                # Filter to selected storm
                storm_data = data[
                    (data['name'] == storm_name) & 
                    (data['year'] == year)
                ]
            else:
                storm_data = data[data['name'] == storm_info]
        else:
            # Use first available storm
            if not data.empty:
                first_storm = data.groupby(['name', 'year']).first().index[0]
                storm_name, year = first_storm
                storm_data = data[
                    (data['name'] == storm_name) & 
                    (data['year'] == year)
                ]
            else:
                storm_data = data
        
        return self._process_regional_tracks(storm_data, selected_storms)
    
    def _plot_multiple_storm_tracks(self, ax, track_data: Dict, selected_storms: List[str] = None):
        """Plot multiple storm tracks on regional map"""
        import matplotlib.colors as mcolors
        
        # Define color scheme for different storm intensities
        colors = {
            'TD': '#74a9cf',      # Light blue - Tropical Depression
            'TS': '#2b8cbe',      # Blue - Tropical Storm
            'H1': '#fdcc8a',      # Light orange - Category 1
            'H2': '#fc8d59',      # Orange - Category 2
            'H3': '#e34a33',      # Red - Category 3
            'H4': '#b30000',      # Dark red - Category 4
            'H5': '#7a0177'       # Purple - Category 5
        }
        
        selected_tracks = []
        regular_tracks = []
        
        # Separate selected and regular tracks
        for storm_key, track in track_data.items():
            if track['is_selected']:
                selected_tracks.append(track)
            else:
                regular_tracks.append(track)
        
        # Plot regular tracks first (background)
        for track in regular_tracks:
            self._plot_single_track_line(ax, track, colors, alpha=0.3, linewidth=1.0)
        
        # Plot selected tracks on top (highlighted)
        for track in selected_tracks:
            self._plot_single_track_line(ax, track, colors, alpha=0.9, linewidth=2.5)
            # Add storm name label
            if track['start_pos']:
                ax.annotate(track['name'], track['start_pos'], 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, fontweight='bold', 
                           bbox=dict(boxstyle='round,pad=0.3', 
                                    facecolor=self.theme.colors.surface if self.theme else 'white', 
                                    alpha=0.8))
    
    def _plot_single_storm_track(self, ax, track_data: Dict, selected_storms: List[str] = None):
        """Plot single storm track with detailed information"""
        if not track_data:
            return
        
        # Get the first (and likely only) track
        track = list(track_data.values())[0]
        
        # Plot detailed track with intensity markers
        lons, lats = track['lons'], track['lats']
        winds = track['winds']
        
        # Create scatter plot with wind speed color coding
        scatter = ax.scatter(lons, lats, c=winds, cmap='YlOrRd', 
                           s=30, alpha=0.8, edgecolors='black', linewidth=0.5)
        
        # Plot track line
        ax.plot(lons, lats, 'k-', linewidth=2, alpha=0.6)
        
        # Mark start and end points
        if len(lons) > 0:
            ax.scatter(lons[0], lats[0], c='green', s=100, marker='^', 
                      label='Start', edgecolors='black', linewidth=1)
            ax.scatter(lons[-1], lats[-1], c='red', s=100, marker='v', 
                      label='End', edgecolors='black', linewidth=1)
        
        # Add colorbar for wind speeds
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, aspect=20)
        cbar.set_label('Wind Speed (mph)', rotation=270, labelpad=15)
    
    def _plot_single_track_line(self, ax, track, colors, alpha=1.0, linewidth=2.0):
        """Plot a single storm track line with category-based coloring"""
        lons, lats = track['lons'], track['lats']
        categories = track['categories']
        
        # Plot track segments with different colors based on category
        for i in range(len(lons) - 1):
            cat = int(categories[i]) if not np.isnan(categories[i]) and categories[i] > 0 else 0
            
            # Determine color based on category
            if cat == 0:
                color = colors['TD']  # Tropical Depression/Storm
            elif cat == 1:
                color = colors['H1']
            elif cat == 2:
                color = colors['H2']
            elif cat == 3:
                color = colors['H3']
            elif cat == 4:
                color = colors['H4']
            elif cat >= 5:
                color = colors['H5']
            else:
                color = colors['TS']
            
            # Plot line segment
            ax.plot([lons[i], lons[i+1]], [lats[i], lats[i+1]], 
                   color=color, linewidth=linewidth, alpha=alpha, solid_capstyle='round')
    
    def _add_gulf_coast_features(self, ax):
        """Add comprehensive geographical features with visible landmasses, state borders, and Caribbean"""
        
        # Define landmass and coastline style
        land_style = dict(facecolor='#f0f4f8', edgecolor='white', linewidth=2.5, alpha=0.8, zorder=1)
        coastline_style = dict(color='white', linewidth=2.5, alpha=0.95, zorder=2)
        state_border_style = dict(color='#e2e8f0', linewidth=1.5, linestyle='--', alpha=0.7, zorder=2)
        
        # === GULF COAST STATES LANDMASSES ===
        
        # Texas (simplified polygon)
        tx_lon = [-106.5, -93.5, -93.5, -94.0, -97.8, -97.4, -96.8, -95.9, -95.3, -94.8, -94.0, -93.8, -93.8, -103.0, -106.5, -106.5]
        tx_lat = [25.8, 25.8, 29.7, 29.8, 26.0, 26.8, 27.8, 28.9, 29.3, 29.6, 29.8, 29.7, 36.5, 36.5, 32.0, 25.8]
        ax.fill(tx_lon, tx_lat, **land_style)
        ax.plot(tx_lon, tx_lat, **coastline_style)
        
        # Louisiana (with detailed coastline and delta)
        la_lon = [-93.8, -89.0, -89.0, -91.2, -93.8, -93.8]
        la_lat = [29.7, 29.0, 33.0, 33.0, 33.0, 29.7]
        ax.fill(la_lon, la_lat, **land_style)
        
        # Louisiana detailed coast
        la_coast_lon = [-93.8, -93.0, -92.2, -91.5, -90.8, -90.0, -89.4, -89.2, -89.0]
        la_coast_lat = [29.7, 29.8, 29.8, 29.6, 29.4, 29.2, 29.1, 29.2, 29.0]
        ax.plot(la_coast_lon, la_coast_lat, **coastline_style)
        
        # Mississippi
        ms_lon = [-91.2, -88.1, -88.1, -91.2, -91.2]
        ms_lat = [33.0, 35.0, 30.2, 33.0, 33.0]
        ax.fill(ms_lon, ms_lat, **land_style)
        
        # Alabama 
        al_lon = [-88.1, -85.0, -85.0, -87.5, -88.1, -88.1]
        al_lat = [35.0, 35.0, 30.2, 30.3, 30.2, 35.0]
        ax.fill(al_lon, al_lat, **land_style)
        
        # Florida (detailed including Keys)
        fl_main_lon = [-87.0, -80.0, -80.0, -80.5, -82.0, -82.5, -83.0, -83.5, -84.2, -85.0, -85.8, -86.5, -87.0, -87.0]
        fl_main_lat = [30.4, 31.0, 24.5, 24.5, 24.5, 27.5, 28.0, 28.5, 29.0, 29.5, 29.8, 30.0, 30.2, 30.4]
        ax.fill(fl_main_lon, fl_main_lat, **land_style)
        ax.plot(fl_main_lon, fl_main_lat, **coastline_style)
        
        # Florida Keys (simplified)
        keys_lon = [-82.0, -80.0, -81.5, -82.0]
        keys_lat = [24.5, 24.5, 24.0, 24.5]
        ax.fill(keys_lon, keys_lat, **land_style)
        ax.plot(keys_lon, keys_lat, **coastline_style)
        
        # === CARIBBEAN ISLANDS ===
        
        # Cuba (northern coast visible)
        cuba_lon = [-85.0, -74.0, -74.0, -85.0, -85.0]
        cuba_lat = [19.8, 19.8, 23.3, 23.3, 19.8]
        ax.fill(cuba_lon, cuba_lat, **land_style)
        ax.plot(cuba_lon, cuba_lat, **coastline_style)
        
        # Bahamas (simplified chain)
        bahamas_islands = [
            ([-78.0, -77.5, -77.5, -78.0, -78.0], [25.0, 25.0, 26.5, 26.5, 25.0]),  # Nassau area
            ([-77.5, -77.0, -77.0, -77.5, -77.5], [24.0, 24.0, 24.5, 24.5, 24.0])   # Other keys
        ]
        for lon, lat in bahamas_islands:
            ax.fill(lon, lat, **land_style)
            ax.plot(lon, lat, **coastline_style)
        
        # Jamaica
        jamaica_lon = [-78.5, -76.0, -76.0, -78.5, -78.5]
        jamaica_lat = [17.7, 17.7, 18.5, 18.5, 17.7]
        ax.fill(jamaica_lon, jamaica_lat, **land_style)
        ax.plot(jamaica_lon, jamaica_lat, **coastline_style)
        
        # Haiti/Dominican Republic (Hispaniola)
        hispaniola_lon = [-74.5, -68.3, -68.3, -74.5, -74.5]
        hispaniola_lat = [18.0, 18.0, 19.9, 19.9, 18.0]
        ax.fill(hispaniola_lon, hispaniola_lat, **land_style)
        ax.plot(hispaniola_lon, hispaniola_lat, **coastline_style)
        
        # Puerto Rico
        pr_lon = [-67.3, -65.2, -65.2, -67.3, -67.3]
        pr_lat = [17.9, 17.9, 18.5, 18.5, 17.9]
        ax.fill(pr_lon, pr_lat, **land_style)
        ax.plot(pr_lon, pr_lat, **coastline_style)
        
        # Lesser Antilles (major islands)
        antilles_islands = [
            ([-61.9, -61.0, -61.0, -61.9, -61.9], [17.0, 17.0, 17.6, 17.6, 17.0]),  # Antigua
            ([-61.4, -61.2, -61.2, -61.4, -61.4], [15.3, 15.3, 15.6, 15.6, 15.3]),  # Dominica
            ([-61.2, -60.8, -60.8, -61.2, -61.2], [14.4, 14.4, 14.9, 14.9, 14.4]),  # Martinique
        ]
        for lon, lat in antilles_islands:
            ax.fill(lon, lat, **land_style)
            ax.plot(lon, lat, **coastline_style)
        
        # === STATE BORDERS ===
        
        # Texas-Louisiana border
        ax.plot([-93.8, -93.8], [29.7, 36.5], **state_border_style)
        
        # Louisiana-Mississippi border
        ax.plot([-91.2, -91.2], [29.0, 35.0], **state_border_style)
        
        # Mississippi-Alabama border
        ax.plot([-88.1, -88.1], [30.2, 35.0], **state_border_style)
        
        # Alabama-Florida border
        ax.plot([-87.0, -85.0], [31.0, 31.0], **state_border_style)
        ax.plot([-87.0, -87.0], [30.4, 31.0], **state_border_style)
        
        # === MAJOR CITIES ===
        cities = {
            'Houston': (-95.37, 29.76),
            'New Orleans': (-90.07, 29.95),
            'Mobile': (-88.04, 30.69),
            'Tampa': (-82.46, 27.95),
            'Miami': (-80.19, 25.76),
            'Havana': (-82.35, 23.13),
            'Nassau': (-77.35, 25.08)
        }
        
        for city, (lon, lat) in cities.items():
            ax.plot(lon, lat, 'o', markersize=5, markerfacecolor='#e53e3e', 
                   markeredgecolor='white', markeredgewidth=1.5, zorder=5)
            ax.annotate(city, (lon, lat), xytext=(4, 4), textcoords='offset points',
                       fontsize=9, fontweight='bold', color='#2d3748', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
        
        # Add state boundaries (simplified)
        # TX-LA border
        ax.plot([-94.0, -94.0], [29.0, 33.0], 'k--', alpha=0.4, linewidth=1)
        # LA-MS border  
        ax.plot([-91.4, -91.4], [29.0, 33.0], 'k--', alpha=0.4, linewidth=1)
        # MS-AL border
        ax.plot([-88.5, -88.5], [30.0, 35.0], 'k--', alpha=0.4, linewidth=1)
        # AL-FL border
        ax.plot([-87.5, -87.5], [30.0, 31.0], 'k--', alpha=0.4, linewidth=1)
        
        # Add grid for better reference
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=1, color='gray')
    
    def _set_regional_boundaries(self, ax, data: pd.DataFrame):
        """Set appropriate map boundaries for Gulf Coast region"""
        if data.empty:
            # Default Gulf Coast view
            ax.set_xlim(-100, -80)
            ax.set_ylim(24, 32)
        else:
            # Calculate boundaries based on data with padding
            lon_min, lon_max = data['long'].min(), data['long'].max()
            lat_min, lat_max = data['lat'].min(), data['lat'].max()
            
            # Add padding
            lon_padding = (lon_max - lon_min) * 0.1
            lat_padding = (lat_max - lat_min) * 0.1
            
            # Ensure we include the Gulf Coast region
            lon_min = min(lon_min - lon_padding, -100)
            lon_max = max(lon_max + lon_padding, -80)
            lat_min = max(lat_min - lat_padding, 20)  # Don't go too far south
            lat_max = min(lat_max + lat_padding, 35)   # Don't go too far north
            
            ax.set_xlim(lon_min, lon_max)
            ax.set_ylim(lat_min, lat_max)
        
        # Set aspect ratio for proper geographic projection
        # Use 'datalim' to maintain proper geographic proportions while fitting the container
        ax.set_aspect('equal', adjustable='datalim')
    
    def _add_map_legend_and_labels(self, ax, data: pd.DataFrame):
        """Add legend and labels to the regional map"""
        # Set labels
        ax.set_xlabel('Longitude (°W)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
        
        # Format tick labels
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Add legend for storm categories
        legend_elements = [
            plt.Line2D([0], [0], color='#74a9cf', lw=3, label='Tropical Depression'),
            plt.Line2D([0], [0], color='#2b8cbe', lw=3, label='Tropical Storm'),
            plt.Line2D([0], [0], color='#fdcc8a', lw=3, label='Category 1'),
            plt.Line2D([0], [0], color='#fc8d59', lw=3, label='Category 2'),
            plt.Line2D([0], [0], color='#e34a33', lw=3, label='Category 3'),
            plt.Line2D([0], [0], color='#b30000', lw=3, label='Category 4'),
            plt.Line2D([0], [0], color='#7a0177', lw=3, label='Category 5')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', 
                 bbox_to_anchor=(1.0, 1.0), fontsize=9)
    
    def _style_regional_map(self, ax, data: pd.DataFrame):
        """Apply styling optimized for Linux Mint display"""
        # Set background color using theme
        chart_bg = self.theme.colors.chart_bg if self.theme else '#f7f9fc'
        ax.set_facecolor(chart_bg)
        
        # Style the plot area
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.5)
        ax.spines['left'].set_linewidth(1.5)
        
        # Set title
        storm_count = len(data.groupby(['name', 'year'])) if not data.empty else 0
        ax.set_title(f'Gulf Coast Hurricane Tracks - {storm_count} Storms', 
                    fontsize=14, fontweight='bold', pad=15)
    
    def _add_regional_interactivity(self, ax, canvas, track_data: Dict):
        """Add interactive features optimized for Linux Mint"""
        
        def on_click(event):
            """Handle mouse clicks for storm information"""
            if event.inaxes != ax or not track_data:
                return
            
            click_lon, click_lat = event.xdata, event.ydata
            if click_lon is None or click_lat is None:
                return
            
            # Find nearest storm track
            min_dist = float('inf')
            nearest_storm = None
            
            for storm_key, track in track_data.items():
                for lon, lat in zip(track['lons'], track['lats']):
                    dist = ((lon - click_lon) ** 2 + (lat - click_lat) ** 2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        nearest_storm = track
            
            # Show storm info if click is close enough
            if min_dist < 1.0 and nearest_storm:  # Within ~1 degree
                info_text = f"Storm: {nearest_storm['name']}\nMax Wind: {nearest_storm['max_wind']} mph"
                ax.annotate(info_text, (click_lon, click_lat),
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                           fontsize=10, fontweight='bold')
                canvas.draw_idle()
        
        def on_scroll(event):
            """Handle mouse wheel for zooming"""
            if event.inaxes != ax:
                return
            
            scale_factor = 1.1 if event.button == 'up' else 0.9
            
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            
            # Calculate new limits
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            x_range = (xlim[1] - xlim[0]) * scale_factor / 2
            y_range = (ylim[1] - ylim[0]) * scale_factor / 2
            
            ax.set_xlim(x_center - x_range, x_center + x_range)
            ax.set_ylim(y_center - y_range, y_center + y_range)
            canvas.draw_idle()
        
        # Connect events
        canvas.mpl_connect('button_press_event', on_click)
        canvas.mpl_connect('scroll_event', on_scroll)
    
    def generate_analysis_visualization(self, data: pd.DataFrame, 
                                      parent_frame, selected_storms: List[str] = None) -> Dict[str, Any]:
        """Generate native analysis visualization with matplotlib"""
        import time
        start_time = time.time()
        
        if data.empty:
            return self._create_empty_plot(parent_frame, "analysis", "No data available for analysis")
        
        # Create embedded canvas with subplots
        fig, canvas = self.create_embedded_canvas(parent_frame, "analysis")
        
        # Clear any existing plots
        fig.clear()
        
        # Create subplots for multiple analyses
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Category distribution
        ax1 = fig.add_subplot(gs[0, 0])
        self._apply_theme_to_axes(ax1)
        self._plot_category_distribution(ax1, data)
        
        # Intensity over time
        ax2 = fig.add_subplot(gs[0, 1])
        self._apply_theme_to_axes(ax2)
        self._plot_intensity_trends(ax2, data)
        
        # Monthly activity
        ax3 = fig.add_subplot(gs[1, 0])
        self._apply_theme_to_axes(ax3)
        self._plot_monthly_activity(ax3, data)
        
        # Wind speed distribution
        ax4 = fig.add_subplot(gs[1, 1])
        self._apply_theme_to_axes(ax4)
        self._plot_wind_distribution(ax4, data)
        
        # Add overall title
        fig.suptitle('Hurricane Statistical Analysis', 
                    color=self.config.title_color, 
                    fontsize=14, fontweight='bold')
        
        # Update canvas
        canvas.draw_idle()
        
        # Performance tracking
        render_time = time.time() - start_time
        self.render_times['analysis'] = render_time
        
        return {
            'figure': fig,
            'canvas': canvas,
            'data_summary': {
                'total_storms': len(data.groupby(['name', 'year'])),
                'analysis_categories': 4,
                'render_time_ms': render_time * 1000
            }
        }
    
    def update_plot_selection(self, plot_type: str, selected_storms: List[str]):
        """Update plot with new storm selection without full redraw"""
        self.selected_storms = selected_storms
        
        if plot_type in self.active_figures:
            # Trigger efficient redraw of highlights only
            self._update_plot_highlights(plot_type)
    
    def _process_timeline_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process data for timeline visualization"""
        # Group by year and count storms (use lowercase column names)
        yearly_storms = data.groupby('year')['name'].nunique().reset_index()
        yearly_storms.columns = ['year', 'storm_count']
        
        # Fill missing years with zero
        year_range = range(int(data['year'].min()), int(data['year'].max()) + 1)
        all_years = pd.DataFrame({'year': year_range})
        yearly_data = all_years.merge(yearly_storms, on='year', how='left').fillna(0)
        
        return yearly_data
    
    def _process_map_data(self, data: pd.DataFrame) -> List[Dict]:
        """Process data for map visualization"""
        tracks = []
        
        for storm_name in data['name'].unique():
            storm_data = data[data['name'] == storm_name].sort_values('datetime')
            
            if len(storm_data) > 1:  # Only include storms with multiple points
                tracks.append({
                    'name': storm_name,
                    'year': storm_data['year'].iloc[0],
                    'lats': storm_data['lat'].values,
                    'lons': storm_data['long'].values,  # Note: 'long' not 'lon'
                    'winds': storm_data['wind'].values,
                    'categories': storm_data['category'].values
                })
        
        return tracks
    
    def _plot_storm_tracks(self, ax, track_data: List[Dict], selected_storms: List[str] = None):
        """Plot storm tracks using efficient LineCollection"""
        lines = []
        colors = []
        linewidths = []
        
        for track in track_data:
            if len(track['lats']) < 2:
                continue
                
            # Create line segments
            points = np.column_stack([track['lons'], track['lats']])
            
            # Determine color based on selection and intensity
            if selected_storms and track['name'] in selected_storms:
                color = self.config.highlight_color
                linewidth = 2.5
            else:
                # Color by max wind speed
                max_wind = np.max(track['winds'])
                if max_wind >= 157:  # Cat 5
                    color = '#ff0000'
                elif max_wind >= 130:  # Cat 4
                    color = '#ff4500'
                elif max_wind >= 111:  # Cat 3
                    color = '#ffa500'
                elif max_wind >= 96:   # Cat 2
                    color = '#ffff00'
                elif max_wind >= 74:   # Cat 1
                    color = '#90ee90'
                else:  # Tropical Storm
                    color = '#87ceeb'
                linewidth = 1.5
            
            lines.append(points)
            colors.append(color)
            linewidths.append(linewidth)
        
        # Create LineCollection for efficient rendering
        if lines:
            lc = LineCollection(lines, colors=colors, linewidths=linewidths, alpha=0.8)
            ax.add_collection(lc)
    
    def _add_map_features(self, ax, data: pd.DataFrame):
        """Add coastline and geographic features"""
        # Get data bounds (use lowercase column names)
        lat_min, lat_max = data['lat'].min() - 2, data['lat'].max() + 2
        lon_min, lon_max = data['long'].min() - 2, data['long'].max() + 2
        
        # Simple coastline approximation (Gulf Coast)
        gulf_coast_lons = np.array([-97.5, -95.0, -90.0, -85.0, -82.5, -80.0])
        gulf_coast_lats = np.array([25.8, 29.0, 30.0, 30.5, 28.0, 25.5])
        
        ax.plot(gulf_coast_lons, gulf_coast_lats, 
               color='#8B4513', linewidth=3, alpha=0.8, label='Gulf Coast')
        
        # Add grid
        ax.grid(True, alpha=0.3, color=self.config.grid_color)
        
        # Set bounds
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
    
    def _highlight_timeline_storms(self, ax, data: pd.DataFrame, 
                                 selected_storms: List[str], years: np.ndarray, counts: np.ndarray):
        """Highlight selected storms on timeline"""
        for storm in selected_storms:
            storm_data = data[data['name'] == storm]
            if not storm_data.empty:
                storm_years = storm_data['year'].unique()
                for year in storm_years:
                    if year in years:
                        year_idx = np.where(years == year)[0]
                        if len(year_idx) > 0:
                            ax.scatter(year, counts[year_idx[0]], 
                                     color=self.config.highlight_color,
                                     s=100, alpha=0.9, zorder=10,
                                     edgecolor='white', linewidth=2)
    
    def _highlight_map_storms(self, ax, data: pd.DataFrame, selected_storms: List[str]):
        """Highlight selected storms on map"""
        for storm in selected_storms:
            storm_data = data[data['name'] == storm]
            if not storm_data.empty:
                # Plot highlighted track with thicker line
                ax.plot(storm_data['long'], storm_data['lat'],
                       color=self.config.highlight_color,
                       linewidth=3, alpha=0.9, zorder=10)
                
                # Mark start and end points
                start_lon, start_lat = storm_data.iloc[0]['long'], storm_data.iloc[0]['lat']
                end_lon, end_lat = storm_data.iloc[-1]['long'], storm_data.iloc[-1]['lat']
                
                ax.scatter(start_lon, start_lat, color='green', s=80, 
                          marker='o', zorder=11, edgecolor='white', linewidth=2)
                ax.scatter(end_lon, end_lat, color='red', s=80, 
                          marker='s', zorder=11, edgecolor='white', linewidth=2)
    
    def _style_timeline_plot(self, ax, yearly_data: pd.DataFrame):
        """Style the timeline plot"""
        ax.set_xlabel('Year', color=self.config.text_color, fontsize=11)
        ax.set_ylabel('Number of Storms', color=self.config.text_color, fontsize=11)
        ax.set_title('Annual Hurricane Activity Timeline', 
                    color=self.config.title_color, fontsize=13, fontweight='bold', pad=20)
        
        # Format x-axis
        ax.tick_params(colors=self.config.text_color)
        years = yearly_data['year'].values
        if len(years) > 20:
            # Show every 5th year if too many years
            ax.set_xticks(years[::5])
        
        # Add grid
        ax.grid(True, alpha=0.3, color=self.config.grid_color)
        
        # Legend
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Add statistics text
        avg_storms = yearly_data['storm_count'].mean()
        max_storms = yearly_data['storm_count'].max()
        ax.text(0.02, 0.98, f'Avg: {avg_storms:.1f} storms/year\nMax: {int(max_storms)} storms',
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
               color=self.config.text_color, fontsize=10)
    
    def _style_map_plot(self, ax, data: pd.DataFrame):
        """Style the map plot"""
        ax.set_xlabel('Longitude', color=self.config.text_color, fontsize=11)
        ax.set_ylabel('Latitude', color=self.config.text_color, fontsize=11)
        ax.set_title('Hurricane Track Map', 
                    color=self.config.title_color, fontsize=13, fontweight='bold', pad=20)
        
        ax.tick_params(colors=self.config.text_color)
        ax.set_aspect('equal', adjustable='box')
        
        # Add legend for categories
        legend_elements = [
            plt.Line2D([0], [0], color='#87ceeb', lw=2, label='Tropical Storm'),
            plt.Line2D([0], [0], color='#90ee90', lw=2, label='Category 1'),
            plt.Line2D([0], [0], color='#ffff00', lw=2, label='Category 2'),
            plt.Line2D([0], [0], color='#ffa500', lw=2, label='Category 3'),
            plt.Line2D([0], [0], color='#ff4500', lw=2, label='Category 4'),
            plt.Line2D([0], [0], color='#ff0000', lw=2, label='Category 5'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9, fontsize=9)
    
    def _plot_category_distribution(self, ax, data: pd.DataFrame):
        """Plot hurricane category distribution"""
        category_counts = data['category'].value_counts().sort_index()
        
        colors = ['#87ceeb', '#90ee90', '#ffff00', '#ffa500', '#ff4500', '#ff0000']
        bars = ax.bar(category_counts.index, category_counts.values, 
                     color=colors[:len(category_counts)], alpha=0.8)
        
        ax.set_xlabel('Category', color=self.config.text_color)
        ax.set_ylabel('Count', color=self.config.text_color)
        ax.set_title('Category Distribution', color=self.config.title_color, fontweight='bold')
        ax.tick_params(colors=self.config.text_color)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom',
                   color=self.config.text_color, fontsize=9)
    
    def _plot_intensity_trends(self, ax, data: pd.DataFrame):
        """Plot intensity trends over time"""
        yearly_intensity = data.groupby('year')['wind'].mean()
        
        ax.plot(yearly_intensity.index, yearly_intensity.values,
               color=self.config.primary_color, linewidth=2, marker='o', markersize=3)
        
        ax.set_xlabel('Year', color=self.config.text_color)
        ax.set_ylabel('Average Wind Speed (mph)', color=self.config.text_color)
        ax.set_title('Intensity Trends', color=self.config.title_color, fontweight='bold')
        ax.tick_params(colors=self.config.text_color)
        ax.grid(True, alpha=0.3)
    
    def _plot_monthly_activity(self, ax, data: pd.DataFrame):
        """Plot monthly hurricane activity"""
        monthly_counts = data.groupby('month')['name'].nunique()
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        bars = ax.bar(monthly_counts.index, monthly_counts.values,
                     color=self.config.secondary_color, alpha=0.8)
        
        ax.set_xlabel('Month', color=self.config.text_color)
        ax.set_ylabel('Storm Count', color=self.config.text_color)
        ax.set_title('Monthly Activity', color=self.config.title_color, fontweight='bold')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels([month_names[i-1] for i in range(1, 13)], rotation=45)
        ax.tick_params(colors=self.config.text_color)
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_wind_distribution(self, ax, data: pd.DataFrame):
        """Plot wind speed distribution"""
        wind_speeds = data['wind'].dropna()
        
        ax.hist(wind_speeds, bins=30, color=self.config.primary_color, 
               alpha=0.7, edgecolor='black', linewidth=0.5)
        
        ax.set_xlabel('Wind Speed (mph)', color=self.config.text_color)
        ax.set_ylabel('Frequency', color=self.config.text_color)
        ax.set_title('Wind Speed Distribution', color=self.config.title_color, fontweight='bold')
        ax.tick_params(colors=self.config.text_color)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add vertical lines for category thresholds
        thresholds = [74, 96, 111, 130, 157]
        for threshold in thresholds:
            ax.axvline(x=threshold, color='red', linestyle='--', alpha=0.5)
    
    def _add_timeline_interactivity(self, ax, canvas, yearly_data: pd.DataFrame):
        """Add interactive features to timeline plot"""
        def on_hover(event):
            if event.inaxes == ax and event.xdata is not None:
                year = int(round(event.xdata))
                year_data = yearly_data[yearly_data['year'] == year]
                if not year_data.empty:
                    storm_count = year_data['storm_count'].iloc[0]
                    ax.set_title(f'Annual Hurricane Activity Timeline - {year}: {int(storm_count)} storms',
                               color=self.config.title_color, fontsize=13, fontweight='bold')
                    canvas.draw_idle()
        
        canvas.mpl_connect('motion_notify_event', on_hover)
    
    def _add_map_interactivity(self, ax, canvas, track_data: List[Dict]):
        """Add interactive features to map plot"""
        def on_click(event):
            if event.inaxes == ax and event.xdata is not None:
                # Find closest storm track
                click_lon, click_lat = event.xdata, event.ydata
                closest_storm = None
                min_distance = float('inf')
                
                for track in track_data:
                    for lon, lat in zip(track['lons'], track['lats']):
                        distance = np.sqrt((lon - click_lon)**2 + (lat - click_lat)**2)
                        if distance < min_distance:
                            min_distance = distance
                            closest_storm = track['name']
                
                if closest_storm and min_distance < 2.0:  # Within reasonable distance
                    ax.set_title(f'Hurricane Track Map - Selected: {closest_storm}',
                               color=self.config.title_color, fontsize=13, fontweight='bold')
                    canvas.draw_idle()
        
        canvas.mpl_connect('button_press_event', on_click)
    
    def _create_empty_plot(self, parent_frame, plot_type: str, message: str) -> Dict[str, Any]:
        """Create an empty plot with message"""
        fig, canvas = self.create_embedded_canvas(parent_frame, plot_type)
        
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, transform=ax.transAxes,
               horizontalalignment='center', verticalalignment='center',
               fontsize=14, color=self.config.text_color,
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
        ax.set_xticks([])
        ax.set_yticks([])
        
        canvas.draw_idle()
        
        return {
            'figure': fig,
            'canvas': canvas,
            'data_summary': {'empty': True, 'message': message}
        }
    
    def _update_plot_highlights(self, plot_type: str):
        """Update plot highlights without full redraw"""
        if plot_type in self.active_canvases:
            canvas = self.active_canvases[plot_type]
            # Trigger efficient redraw
            canvas.draw_idle()
    
    def _get_geographic_bounds(self, data: pd.DataFrame) -> Dict[str, float]:
        """Get geographic bounds of data"""
        return {
            'lat_min': float(data['lat'].min()),
            'lat_max': float(data['lat'].max()),
            'lon_min': float(data['long'].min()),
            'lon_max': float(data['long'].max())
        }
    
    def _on_canvas_draw(self, event):
        """Handle canvas draw events for performance monitoring"""
        canvas = event.canvas
        # Could add performance monitoring here if needed
        pass
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'render_times_ms': self.render_times,
            'active_plots': list(self.active_figures.keys()),
            'cache_size': len(self.data_cache),
            'memory_usage': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of active plots"""
        # Simple estimation based on number of active figures
        estimate_mb = len(self.active_figures) * 5  # Rough estimate
        return f"{estimate_mb} MB"
    
    def cleanup(self):
        """Clean up resources"""
        try:
            for canvas in self.active_canvases.values():
                try:
                    if hasattr(canvas, 'get_tk_widget'):
                        widget = canvas.get_tk_widget()
                        if widget.winfo_exists():
                            widget.destroy()
                except Exception:
                    pass  # Widget already destroyed
            
            for fig in self.active_figures.values():
                try:
                    plt.close(fig)
                except Exception:
                    pass
            
            self.active_figures.clear()
            self.active_canvases.clear()
            self.active_toolbars.clear()
            
            print("✅ Native visualization engine cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    # Wrapper methods for enhanced dashboard compatibility
    def create_timeline_visualization(self, data: pd.DataFrame, parent_frame, 
                                    title: str = "Timeline", settings: Optional[VisualizationSettings] = None):
        """Create timeline visualization with settings"""
        if settings:
            # Update engine settings
            self.settings = settings
            configure_matplotlib(settings)
        
        return self.generate_timeline_visualization(data, parent_frame, [])
    
    def create_map_visualization(self, data: pd.DataFrame, parent_frame,
                               title: str = "Map", settings: Optional[VisualizationSettings] = None):
        """Create map visualization with settings"""
        if settings:
            self.settings = settings
            configure_matplotlib(settings)
        
        return self.generate_map_visualization(data, parent_frame, [])
    
    def create_analysis_visualization(self, data: pd.DataFrame, parent_frame,
                                    analysis_type: str = "category_distribution",
                                    chart_type: str = "bar",
                                    settings: Optional[VisualizationSettings] = None):
        """Create analysis visualization with settings"""
        if settings:
            self.settings = settings
            configure_matplotlib(settings)
        
        # Call the correct method signature - only pass data, parent_frame, and selected_storms
        return self.generate_analysis_visualization(data, parent_frame, [])