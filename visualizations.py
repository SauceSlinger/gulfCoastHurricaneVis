"""
Visualization Components for Hurricane Dashboard
Creates interactive Plotly visualizations for timeline, maps, and analysis
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

class HurricaneVisualizations:
    """Create interactive visualizations for hurricane data"""
    
    def __init__(self):
        """Initialize visualization settings"""
        # Color schemes for different hurricane categories
        self.category_colors = {
            1: '#74add1',     # Light blue
            2: '#4575b4',     # Blue  
            3: '#fee90d',     # Yellow
            4: '#fd8d3c',     # Orange
            5: '#bd0026',     # Red
            'tropical_storm': '#a6cee3',
            'tropical_depression': '#b2df8a'
        }
        
        # Map styling
        self.map_style = "carto-positron"  # Clean map style
        
        # Different map centers for different scopes
        self.gulf_center = {'lat': 27.5, 'lon': -89.0}
        self.atlantic_center = {'lat': 35.0, 'lon': -65.0}  # Broader Atlantic view
        
        # Geographic boundaries for different views
        self.gulf_bounds = {
            'lat_min': 24.0, 'lat_max': 31.0,
            'lon_min': -98.0, 'lon_max': -80.0
        }
        
        self.atlantic_bounds = {
            'lat_min': 7.0, 'lat_max': 70.7,
            'lon_min': -109.3, 'lon_max': 13.5
        }
    
    def create_timeline_overview(self, annual_data: pd.DataFrame, 
                                title: str = "Gulf Coast Hurricane Timeline") -> go.Figure:
        """Create an interactive timeline showing hurricane activity over years"""
        
        if annual_data is None or len(annual_data) == 0:
            return self._create_empty_plot("No data available for timeline")
        
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=('Annual Hurricane Activity', 'Storm Intensity Distribution'),
            vertical_spacing=0.1
        )
        
        # Main timeline chart (top)
        fig.add_trace(
            go.Scatter(
                x=annual_data['year'],
                y=annual_data['storm_count'],
                mode='lines+markers',
                name='Number of Storms',
                line=dict(color='#2E86C1', width=3),
                marker=dict(size=8, color='#2E86C1'),
                hovertemplate='<b>%{x}</b><br>Storms: %{y}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add trend line
        if len(annual_data) > 3:
            z = np.polyfit(annual_data['year'], annual_data['storm_count'], 1)
            trend_line = np.poly1d(z)
            fig.add_trace(
                go.Scatter(
                    x=annual_data['year'],
                    y=trend_line(annual_data['year']),
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=2, dash='dash'),
                    hovertemplate='<b>Trend Line</b><extra></extra>'
                ),
                row=1, col=1
            )
        
        # Average line
        avg_storms = annual_data['storm_count'].mean()
        fig.add_hline(
            y=avg_storms, 
            line_dash="dot", 
            line_color="gray",
            annotation_text=f"Average: {avg_storms:.1f} storms/year",
            row=1, col=1
        )
        
        # Wind speed distribution (bottom)
        if 'max_wind' in annual_data.columns:
            fig.add_trace(
                go.Bar(
                    x=annual_data['year'],
                    y=annual_data['max_wind'],
                    name='Max Wind Speed (mph)',
                    marker_color='orange',
                    opacity=0.7,
                    hovertemplate='<b>%{x}</b><br>Max Wind: %{y} mph<extra></extra>'
                ),
                row=2, col=1
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            template='plotly_white',
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Update axes
        fig.update_xaxes(title_text="Year", row=2, col=1)
        fig.update_yaxes(title_text="Number of Storms", row=1, col=1)
        fig.update_yaxes(title_text="Wind Speed (mph)", row=2, col=1)
        
        return fig
    
    def create_storm_track_map(self, storm_tracks: Dict, 
                              title: str = "Hurricane Tracks - Full Atlantic Basin",
                              map_scope: str = "atlantic") -> go.Figure:
        """Create an interactive map showing hurricane tracks with flexible scope"""
        
        if not storm_tracks:
            return self._create_empty_plot("No storm track data available")
        
        fig = go.Figure()
        
        # Determine map center and zoom based on scope
        if map_scope == "gulf":
            center = self.gulf_center
            zoom = 5
            bounds = self.gulf_bounds
            boundary_name = "Gulf Coast Region"
        else:  # atlantic scope
            center = self.atlantic_center
            zoom = 3
            bounds = self.atlantic_bounds
            boundary_name = "Atlantic Basin Coverage"
        
        # Add each storm track
        for storm_id, track_data in storm_tracks.items():
            if not track_data['lats'] or not track_data['lons']:
                continue
            
            # Determine track color based on max wind speed
            max_wind = track_data.get('max_wind', 0)
            color = self._get_wind_color(max_wind)
            
            # Create hover text with storm details
            hover_text = []
            for i in range(len(track_data['lats'])):
                wind = track_data['winds'][i] if i < len(track_data['winds']) else 'N/A'
                pressure = track_data['pressures'][i] if i < len(track_data['pressures']) else 'N/A'
                dt = track_data['datetimes'][i] if i < len(track_data['datetimes']) else 'N/A'
                
                hover_text.append(
                    f"<b>{track_data['name']}</b><br>"
                    f"Date: {dt}<br>"
                    f"Wind: {wind} mph<br>"
                    f"Pressure: {pressure} mb"
                )
            
            # Add storm track
            fig.add_trace(
                go.Scattermapbox(
                    lat=track_data['lats'],
                    lon=track_data['lons'],
                    mode='lines+markers',
                    name=track_data['name'],
                    line=dict(width=3, color=color),
                    marker=dict(size=4, color=color),
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=hover_text
                )
            )
        
        # Add boundary box for reference
        boundary_lats = [bounds['lat_min'], bounds['lat_max'], 
                        bounds['lat_max'], bounds['lat_min'], 
                        bounds['lat_min']]
        boundary_lons = [bounds['lon_min'], bounds['lon_min'], 
                        bounds['lon_max'], bounds['lon_max'], 
                        bounds['lon_min']]
        
        fig.add_trace(
            go.Scattermapbox(
                lat=boundary_lats,
                lon=boundary_lons,
                mode='lines',
                name=boundary_name,
                line=dict(width=2, color='red'),
                hoverinfo='skip'
            )
        )
        
        # Add major geographic markers for context
        if map_scope == "atlantic":
            # Add some major cities/landmarks for reference
            landmarks = [
                {'name': 'Miami, FL', 'lat': 25.7617, 'lon': -80.1918},
                {'name': 'New Orleans, LA', 'lat': 29.9511, 'lon': -90.0715},
                {'name': 'Houston, TX', 'lat': 29.7604, 'lon': -95.3698},
                {'name': 'Bermuda', 'lat': 32.3078, 'lon': -64.7505},
                {'name': 'Cabo Verde', 'lat': 16.5388, 'lon': -23.0342}
            ]
            
            landmark_lats = [l['lat'] for l in landmarks]
            landmark_lons = [l['lon'] for l in landmarks]
            landmark_names = [l['name'] for l in landmarks]
            
            fig.add_trace(
                go.Scattermapbox(
                    lat=landmark_lats,
                    lon=landmark_lons,
                    mode='markers+text',
                    name='Reference Points',
                    marker=dict(size=8, color='black', symbol='circle'),
                    text=landmark_names,
                    textposition='top center',
                    textfont=dict(size=10, color='black'),
                    hovertemplate='%{text}<extra></extra>'
                )
            )
        
        # Update layout for map
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            mapbox=dict(
                style=self.map_style,
                center=center,
                zoom=zoom
            ),
            height=600,
            margin=dict(l=0, r=0, t=50, b=0),
            showlegend=False  # Too many storms would clutter the legend
        )
        
        return fig
    
    def create_impact_heatmap(self, impact_stats: Dict, 
                             title: str = "Hurricane Impact Frequency Heatmap") -> go.Figure:
        """Create a heatmap showing hurricane impact frequency by geographic region"""
        
        if not impact_stats or 'impact_grid' not in impact_stats:
            return self._create_empty_plot("No impact data available")
        
        impact_grid = impact_stats['impact_grid']
        lat_bins = impact_stats['lat_bins']
        lon_bins = impact_stats['lon_bins']
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=impact_grid,
            x=[f"{lon:.1f}" for lon in lon_bins[:-1]],
            y=[f"{lat:.1f}" for lat in lat_bins[:-1]],
            colorscale='YlOrRd',
            hovertemplate='<b>Lat: %{y}°N</b><br>Lon: %{x}°W<br>Storm Count: %{z}<extra></extra>',
            colorbar=dict(title="Number of Storms")
        ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def create_seasonal_analysis(self, data: pd.DataFrame, 
                                title: str = "Hurricane Seasonal Patterns") -> go.Figure:
        """Create visualization showing seasonal hurricane patterns"""
        
        if data is None or len(data) == 0:
            return self._create_empty_plot("No seasonal data available")
        
        # Monthly storm frequency
        monthly_counts = data.groupby('month')['name'].nunique().reindex(range(1, 13), fill_value=0)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Create subplot with polar and cartesian plots
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.6, 0.4],
            subplot_titles=('Monthly Hurricane Activity', 'Peak Season Analysis'),
            specs=[[{"secondary_y": False}, {"type": "polar"}]]
        )
        
        # Bar chart for monthly activity
        fig.add_trace(
            go.Bar(
                x=month_names,
                y=monthly_counts.values,
                name='Storm Count',
                marker_color=['lightblue' if i < 5 or i > 10 else 'orange' if i < 7 else 'red' 
                             for i in range(12)],
                hovertemplate='<b>%{x}</b><br>Storms: %{y}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Polar plot for seasonal cycle
        fig.add_trace(
            go.Scatterpolar(
                r=monthly_counts.values,
                theta=month_names,
                mode='lines+markers',
                name='Seasonal Cycle',
                line=dict(color='red', width=3),
                marker=dict(size=8, color='red'),
                fill='toself',
                fillcolor='rgba(255,0,0,0.1)'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        # Update axes
        fig.update_xaxes(title_text="Month", row=1, col=1)
        fig.update_yaxes(title_text="Number of Storms", row=1, col=1)
        
        return fig
    
    def create_intensity_analysis(self, data: pd.DataFrame, 
                                 title: str = "Hurricane Intensity Analysis") -> go.Figure:
        """Create analysis of hurricane intensity patterns"""
        
        if data is None or len(data) == 0:
            return self._create_empty_plot("No intensity data available")
        
        # Create subplots for different intensity metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Wind Speed Distribution', 'Pressure vs Wind Speed',
                'Category Distribution', 'Intensity Over Time'
            ),
            specs=[[{}, {}], [{}, {}]]
        )
        
        # Wind speed histogram
        fig.add_trace(
            go.Histogram(
                x=data['wind'].dropna(),
                nbinsx=30,
                name='Wind Speed',
                marker_color='skyblue',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Pressure vs Wind Speed scatter
        valid_data = data.dropna(subset=['wind', 'pressure'])
        if len(valid_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=valid_data['wind'],
                    y=valid_data['pressure'],
                    mode='markers',
                    name='Pressure vs Wind',
                    marker=dict(
                        size=5,
                        color=valid_data['wind'],
                        colorscale='Viridis',
                        opacity=0.6
                    ),
                    hovertemplate='Wind: %{x} mph<br>Pressure: %{y} mb<extra></extra>'
                ),
                row=1, col=2
            )
        
        # Category distribution
        if 'category' in data.columns:
            category_counts = data['category'].value_counts().sort_index()
            fig.add_trace(
                go.Bar(
                    x=[f"Cat {int(cat)}" for cat in category_counts.index if not pd.isna(cat)],
                    y=[category_counts[cat] for cat in category_counts.index if not pd.isna(cat)],
                    name='Category Distribution',
                    marker_color=['#74add1', '#4575b4', '#fee90d', '#fd8d3c', '#bd0026'][:len(category_counts)]
                ),
                row=2, col=1
            )
        
        # Intensity over time (by decade)
        data_with_decade = data.copy()
        data_with_decade['decade'] = (data_with_decade['year'] // 10) * 10
        decade_intensity = data_with_decade.groupby('decade')['wind'].mean()
        
        fig.add_trace(
            go.Scatter(
                x=[f"{int(decade)}s" for decade in decade_intensity.index],
                y=decade_intensity.values,
                mode='lines+markers',
                name='Average Intensity by Decade',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            template='plotly_white',
            height=600,
            showlegend=False
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Wind Speed (mph)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_xaxes(title_text="Wind Speed (mph)", row=1, col=2)
        fig.update_yaxes(title_text="Pressure (mb)", row=1, col=2)
        fig.update_xaxes(title_text="Category", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_xaxes(title_text="Decade", row=2, col=2)
        fig.update_yaxes(title_text="Avg Wind Speed (mph)", row=2, col=2)
        
        return fig
    
    def create_summary_dashboard(self, annual_data: pd.DataFrame, 
                                storm_tracks: Dict, 
                                impact_stats: Dict) -> go.Figure:
        """Create a comprehensive summary dashboard"""
        
        # Create a 2x2 subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Annual Storm Activity', 'Recent Storm Tracks',
                'Impact Frequency Heatmap', 'Key Statistics'
            ),
            specs=[
                [{"secondary_y": False}, {"type": "mapbox"}],
                [{"type": "xy"}, {"type": "xy"}]
            ]
        )
        
        # Annual activity (top left)
        if annual_data is not None and len(annual_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=annual_data['year'],
                    y=annual_data['storm_count'],
                    mode='lines+markers',
                    name='Annual Storms',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
        
        # Storm tracks (top right) - Show recent storms only
        if storm_tracks:
            recent_storms = dict(list(storm_tracks.items())[-5:])  # Last 5 storms
            for storm_id, track_data in recent_storms.items():
                if track_data['lats'] and track_data['lons']:
                    color = self._get_wind_color(track_data.get('max_wind', 0))
                    fig.add_trace(
                        go.Scattermapbox(
                            lat=track_data['lats'],
                            lon=track_data['lons'],
                            mode='lines',
                            name=track_data['name'][:10] + '...' if len(track_data['name']) > 10 else track_data['name'],
                            line=dict(width=2, color=color),
                            showlegend=False
                        ),
                        row=1, col=2
                    )
        
        # Impact heatmap (bottom left)
        if impact_stats and 'impact_grid' in impact_stats:
            impact_grid = impact_stats['impact_grid']
            fig.add_trace(
                go.Heatmap(
                    z=impact_grid,
                    colorscale='YlOrRd',
                    showscale=False,
                    hovertemplate='Impact Level: %{z}<extra></extra>'
                ),
                row=2, col=1
            )
        
        # Key statistics (bottom right) - Create a simple text-based summary
        stats_text = self._create_stats_summary(annual_data, storm_tracks, impact_stats)
        fig.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode='text',
                text=[stats_text, ''],
                textposition='middle center',
                showlegend=False,
                textfont=dict(size=12)
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Gulf Coast Hurricane Summary Dashboard',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            template='plotly_white',
            height=700,
            mapbox=dict(
                style=self.map_style,
                center=self.gulf_center,
                zoom=4
            )
        )
        
        return fig
    
    def _get_wind_color(self, wind_speed: float) -> str:
        """Get color based on wind speed"""
        if pd.isna(wind_speed):
            return '#gray'
        elif wind_speed < 39:
            return '#b2df8a'  # Light green
        elif wind_speed < 74:
            return '#a6cee3'  # Light blue  
        elif wind_speed < 96:
            return '#74add1'  # Blue
        elif wind_speed < 111:
            return '#4575b4'  # Dark blue
        elif wind_speed < 130:
            return '#fee90d'  # Yellow
        elif wind_speed < 157:
            return '#fd8d3c'  # Orange
        else:
            return '#bd0026'  # Red
    
    def _create_empty_plot(self, message: str) -> go.Figure:
        """Create an empty plot with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            template='plotly_white',
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    def _create_stats_summary(self, annual_data: pd.DataFrame, 
                            storm_tracks: Dict, 
                            impact_stats: Dict) -> str:
        """Create a text summary of key statistics"""
        stats = []
        
        if annual_data is not None and len(annual_data) > 0:
            avg_storms = annual_data['storm_count'].mean()
            max_year = annual_data.loc[annual_data['storm_count'].idxmax(), 'year']
            max_storms = annual_data['storm_count'].max()
            
            stats.append(f"Average Storms/Year: {avg_storms:.1f}")
            stats.append(f"Most Active Year: {max_year} ({max_storms} storms)")
        
        if storm_tracks:
            stats.append(f"Total Tracked Storms: {len(storm_tracks)}")
        
        if impact_stats:
            total_storms = impact_stats.get('total_storms', 0)
            stats.append(f"Gulf Coast Impacts: {total_storms}")
        
        return "\n".join(stats) if stats else "No statistics available"

    def create_timeline_overview_with_highlight(self, annual_data: pd.DataFrame, selected_storms: List[str]) -> go.Figure:
        """Create timeline overview with selected storms highlighted"""
        try:
            # Create base timeline
            fig = self.create_timeline_overview(annual_data)
            
            if not selected_storms:
                return fig
            
            # Parse selected storms to get years
            highlighted_years = []
            for storm_id in selected_storms:
                try:
                    year = int(storm_id.split('_')[1])
                    highlighted_years.append(year)
                except (IndexError, ValueError):
                    continue
            
            highlighted_years = list(set(highlighted_years))  # Remove duplicates
            
            if not highlighted_years:
                return fig
            
            # Add highlight bars for selected years
            for year in highlighted_years:
                if year in annual_data['year'].values:
                    storm_count = annual_data[annual_data['year'] == year]['storm_count'].iloc[0]
                    
                    # Add highlight bar
                    fig.add_trace(go.Scatter(
                        x=[year, year],
                        y=[0, storm_count + 1],
                        mode='lines',
                        line=dict(
                            color='rgba(255, 215, 0, 0.8)',  # Gold highlight
                            width=6
                        ),
                        name=f'Highlighted Year: {year}',
                        showlegend=False,
                        hovertemplate=f'<b>Highlighted Year: {year}</b><br>Storms: {storm_count}<extra></extra>'
                    ))
            
            # Update layout to show highlights
            fig.update_layout(
                title=dict(
                    text="Hurricane Activity Timeline (with Selected Storm Highlights)",
                    font=dict(size=20, color='#1f2937')
                )
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating highlighted timeline: {e}")
            # Return base timeline if highlighting fails
            return self.create_timeline_overview(annual_data)
    
    def create_storm_track_map_with_highlight(self, storm_tracks: Dict, selected_storms: List[str], 
                                            title: str = "Hurricane Tracks", map_scope: str = "gulf") -> go.Figure:
        """Create storm track map with selected storms highlighted"""
        try:
            # Create base map
            fig = self.create_storm_track_map(storm_tracks, title, map_scope)
            
            if not selected_storms:
                return fig
            
            # Parse selected storm IDs
            selected_storm_keys = []
            for storm_id in selected_storms:
                parts = storm_id.split('_')
                if len(parts) >= 2:
                    name, year = parts[0], parts[1]
                    # Find matching storm in tracks
                    for key, track in storm_tracks.items():
                        if track['name'].upper() == name.upper() and str(track['year']) == year:
                            selected_storm_keys.append(key)
                            break
            
            if not selected_storm_keys:
                return fig
            
            # Add highlighted tracks for selected storms
            for key in selected_storm_keys:
                if key in storm_tracks:
                    track = storm_tracks[key]
                    
                    # Filter valid coordinates
                    valid_coords = [(lat, lon) for lat, lon in zip(track['lats'], track['lons']) 
                                  if lat is not None and lon is not None and 
                                     not (np.isnan(lat) or np.isnan(lon))]
                    
                    if len(valid_coords) < 2:
                        continue
                    
                    lats, lons = zip(*valid_coords)
                    
                    # Add highlighted storm track
                    fig.add_trace(go.Scattermapbox(
                        lat=lats,
                        lon=lons,
                        mode='lines+markers',
                        line=dict(
                            width=8,
                            color='gold'  # Gold highlight color
                        ),
                        marker=dict(
                            size=12,
                            color='orange',
                            symbol='circle'
                        ),
                        name=f"🌟 {track['name']} ({track['year']}) - HIGHLIGHTED",
                        hovertemplate=(
                            f"<b>🌟 HIGHLIGHTED: {track['name']} ({track['year']})</b><br>"
                            f"Max Category: {track.get('category', 'N/A')}<br>"
                            f"Max Wind: {track.get('max_wind', 0):.0f} mph<br>"
                            f"<i>Lat: %{lat:.2f}°, Lon: %{lon:.2f}°</i>"
                            "<extra></extra>"
                        ),
                        showlegend=True
                    ))
            
            # Update title to show highlighting
            fig.update_layout(
                title=dict(
                    text=f"{title} (with Highlights)",
                    font=dict(size=18, color='#1f2937')
                )
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating highlighted map: {e}")
            # Return base map if highlighting fails
            return self.create_storm_track_map(storm_tracks, title, map_scope)

# Utility function to convert figures to HTML for embedding
def figure_to_html(fig: go.Figure, include_plotlyjs: str = 'inline') -> str:
    """Convert Plotly figure to HTML string for embedding"""
    return fig.to_html(
        include_plotlyjs=include_plotlyjs,
        div_id="plotly-div",
        config={'displayModeBar': True, 'responsive': True}
    )