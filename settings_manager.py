"""
Interactive Settings Manager for Hurricane Dashboard
Provides popup settings panels with gear icons for each visualization component
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path

@dataclass
class VisualizationSettings:
    """Settings for individual visualization components"""
    # Timeline settings
    timeline_show_trend: bool = True
    timeline_show_markers: bool = True
    timeline_line_style: str = "solid"
    timeline_color_scheme: str = "blue"
    timeline_y_scale: str = "linear"
    timeline_grid: bool = True
    
    # Map settings
    map_show_coastline: bool = True
    map_track_width: float = 2.0
    map_show_categories: bool = True
    map_show_markers: bool = True
    map_projection: str = "mercator"
    map_zoom_level: str = "auto"
    
    # Analysis settings
    analysis_show_grid: bool = True
    analysis_color_scheme: str = "viridis"
    analysis_chart_types: Dict[str, str] = field(default_factory=lambda: {
        "category_dist": "bar",
        "intensity_trends": "line", 
        "monthly_activity": "bar",
        "wind_distribution": "histogram"
    })
    analysis_normalize_data: bool = False
    analysis_show_statistics: bool = True
    
    # General settings
    figure_dpi: int = 100
    figure_style: str = "dark_background"
    auto_refresh: bool = True
    show_performance_stats: bool = True

class SettingsPopupWindow:
    """Popup window for visualization settings"""
    
    def __init__(self, parent, title: str, settings: VisualizationSettings, 
                 settings_type: str, callback: Callable = None):
        self.parent = parent
        self.settings = settings
        self.settings_type = settings_type
        self.callback = callback
        
        # Create popup window
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"⚙️ {title} Settings")
        self.window.geometry("400x600")
        self.window.resizable(False, True)
        
        # Make window modal
        self.window.transient(parent)
        
        # Center the window first
        self.center_window()
        
        # Ensure window is visible before grabbing
        self.window.update_idletasks()
        self.window.deiconify()  # Ensure window is visible
        
        # Delay grab to ensure window is fully rendered
        self.window.after(100, self._set_grab)
        
        # Create UI
        self.create_settings_ui()
    
    def _set_grab(self):
        """Set window grab after ensuring it's visible"""
        try:
            self.window.grab_set()
        except Exception as e:
            print(f"⚠️  Could not set window grab: {e}")
        
    def center_window(self):
        """Center the popup window on the parent"""
        self.window.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        window_width = self.window.winfo_reqwidth()
        window_height = self.window.winfo_reqheight()
        
        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)
        
        self.window.geometry(f"+{x}+{y}")
    
    def create_settings_ui(self):
        """Create the settings UI based on visualization type"""
        # Header
        header_frame = ctk.CTkFrame(self.window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"⚙️ {self.settings_type.title()} Visualization Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Scrollable settings frame
        self.settings_frame = ctk.CTkScrollableFrame(self.window, height=400)
        self.settings_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create settings based on type
        if self.settings_type == "timeline":
            self.create_timeline_settings()
        elif self.settings_type == "map":
            self.create_map_settings()
        elif self.settings_type == "analysis":
            self.create_analysis_settings()
        
        # Add general settings for all types
        self.create_general_settings()
        
        # Button frame
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Buttons
        apply_btn = ctk.CTkButton(
            button_frame,
            text="✅ Apply Changes",
            command=self.apply_settings,
            font=ctk.CTkFont(weight="bold"),
            height=35
        )
        apply_btn.pack(side="left", padx=5, pady=5)
        
        reset_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_settings,
            height=35
        )
        reset_btn.pack(side="left", padx=5, pady=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self.close_window,
            height=35
        )
        cancel_btn.pack(side="right", padx=5, pady=5)
    
    def create_timeline_settings(self):
        """Create timeline-specific settings"""
        # Timeline section
        timeline_label = ctk.CTkLabel(
            self.settings_frame,
            text="📈 Timeline Display Options",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        timeline_label.pack(anchor="w", pady=(10, 5))
        
        # Show trend line
        self.trend_var = tk.BooleanVar(value=self.settings.timeline_show_trend)
        trend_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show trend line",
            variable=self.trend_var
        )
        trend_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Show markers
        self.markers_var = tk.BooleanVar(value=self.settings.timeline_show_markers)
        markers_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show data point markers",
            variable=self.markers_var
        )
        markers_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Line style
        line_style_frame = ctk.CTkFrame(self.settings_frame)
        line_style_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(line_style_frame, text="Line style:").pack(side="left", padx=5)
        self.line_style_var = tk.StringVar(value=self.settings.timeline_line_style)
        line_style_menu = ctk.CTkOptionMenu(
            line_style_frame,
            variable=self.line_style_var,
            values=["solid", "dashed", "dotted", "dashdot"]
        )
        line_style_menu.pack(side="right", padx=5)
        
        # Color scheme
        color_frame = ctk.CTkFrame(self.settings_frame)
        color_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(color_frame, text="Color scheme:").pack(side="left", padx=5)
        self.timeline_color_var = tk.StringVar(value=self.settings.timeline_color_scheme)
        color_menu = ctk.CTkOptionMenu(
            color_frame,
            variable=self.timeline_color_var,
            values=["blue", "green", "red", "purple", "orange", "cyan"]
        )
        color_menu.pack(side="right", padx=5)
        
        # Y-axis scale
        scale_frame = ctk.CTkFrame(self.settings_frame)
        scale_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(scale_frame, text="Y-axis scale:").pack(side="left", padx=5)
        self.y_scale_var = tk.StringVar(value=self.settings.timeline_y_scale)
        scale_menu = ctk.CTkOptionMenu(
            scale_frame,
            variable=self.y_scale_var,
            values=["linear", "log"]
        )
        scale_menu.pack(side="right", padx=5)
        
        # Grid
        self.timeline_grid_var = tk.BooleanVar(value=self.settings.timeline_grid)
        grid_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show grid",
            variable=self.timeline_grid_var
        )
        grid_checkbox.pack(anchor="w", padx=10, pady=2)
    
    def create_map_settings(self):
        """Create map-specific settings"""
        # Map section
        map_label = ctk.CTkLabel(
            self.settings_frame,
            text="🗺️ Map Display Options",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        map_label.pack(anchor="w", pady=(10, 5))
        
        # Show coastline
        self.coastline_var = tk.BooleanVar(value=self.settings.map_show_coastline)
        coastline_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show coastline",
            variable=self.coastline_var
        )
        coastline_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Track width
        track_frame = ctk.CTkFrame(self.settings_frame)
        track_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(track_frame, text="Storm track width:").pack(side="left", padx=5)
        self.track_width_var = tk.DoubleVar(value=self.settings.map_track_width)
        track_slider = ctk.CTkSlider(
            track_frame,
            from_=0.5,
            to=5.0,
            variable=self.track_width_var,
            number_of_steps=9
        )
        track_slider.pack(side="right", padx=5)
        
        # Show categories
        self.map_categories_var = tk.BooleanVar(value=self.settings.map_show_categories)
        categories_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Color-code by hurricane category",
            variable=self.map_categories_var
        )
        categories_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Show markers
        self.map_markers_var = tk.BooleanVar(value=self.settings.map_show_markers)
        markers_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show start/end markers",
            variable=self.map_markers_var
        )
        markers_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Projection
        proj_frame = ctk.CTkFrame(self.settings_frame)
        proj_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(proj_frame, text="Map projection:").pack(side="left", padx=5)
        self.projection_var = tk.StringVar(value=self.settings.map_projection)
        proj_menu = ctk.CTkOptionMenu(
            proj_frame,
            variable=self.projection_var,
            values=["mercator", "orthographic", "stereographic", "equirectangular"]
        )
        proj_menu.pack(side="right", padx=5)
    
    def create_analysis_settings(self):
        """Create analysis-specific settings"""
        # Analysis section
        analysis_label = ctk.CTkLabel(
            self.settings_frame,
            text="📊 Analysis Display Options",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        analysis_label.pack(anchor="w", pady=(10, 5))
        
        # Chart type selections
        charts_frame = ctk.CTkFrame(self.settings_frame)
        charts_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(charts_frame, text="Chart Types:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=5)
        
        # Category distribution chart type
        cat_frame = ctk.CTkFrame(charts_frame)
        cat_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(cat_frame, text="Category distribution:").pack(side="left", padx=5)
        self.cat_chart_var = tk.StringVar(value=self.settings.analysis_chart_types["category_dist"])
        cat_menu = ctk.CTkOptionMenu(
            cat_frame,
            variable=self.cat_chart_var,
            values=["bar", "pie", "donut"]
        )
        cat_menu.pack(side="right", padx=5)
        
        # Intensity trends chart type
        int_frame = ctk.CTkFrame(charts_frame)
        int_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(int_frame, text="Intensity trends:").pack(side="left", padx=5)
        self.int_chart_var = tk.StringVar(value=self.settings.analysis_chart_types["intensity_trends"])
        int_menu = ctk.CTkOptionMenu(
            int_frame,
            variable=self.int_chart_var,
            values=["line", "area", "scatter"]
        )
        int_menu.pack(side="right", padx=5)
        
        # Monthly activity chart type
        monthly_frame = ctk.CTkFrame(charts_frame)
        monthly_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(monthly_frame, text="Monthly activity:").pack(side="left", padx=5)
        self.monthly_chart_var = tk.StringVar(value=self.settings.analysis_chart_types["monthly_activity"])
        monthly_menu = ctk.CTkOptionMenu(
            monthly_frame,
            variable=self.monthly_chart_var,
            values=["bar", "line", "polar"]
        )
        monthly_menu.pack(side="right", padx=5)
        
        # Color scheme
        color_frame = ctk.CTkFrame(self.settings_frame)
        color_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(color_frame, text="Color scheme:").pack(side="left", padx=5)
        self.analysis_color_var = tk.StringVar(value=self.settings.analysis_color_scheme)
        analysis_color_menu = ctk.CTkOptionMenu(
            color_frame,
            variable=self.analysis_color_var,
            values=["viridis", "plasma", "inferno", "cool", "warm", "autumn"]
        )
        analysis_color_menu.pack(side="right", padx=5)
        
        # Normalize data
        self.normalize_var = tk.BooleanVar(value=self.settings.analysis_normalize_data)
        normalize_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Normalize data (0-1 scale)",
            variable=self.normalize_var
        )
        normalize_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Show statistics
        self.stats_var = tk.BooleanVar(value=self.settings.analysis_show_statistics)
        stats_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show statistical annotations",
            variable=self.stats_var
        )
        stats_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Grid
        self.analysis_grid_var = tk.BooleanVar(value=self.settings.analysis_show_grid)
        grid_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show grid",
            variable=self.analysis_grid_var
        )
        grid_checkbox.pack(anchor="w", padx=10, pady=2)
    
    def create_general_settings(self):
        """Create general settings for all visualizations"""
        # General section
        general_label = ctk.CTkLabel(
            self.settings_frame,
            text="🔧 General Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        general_label.pack(anchor="w", pady=(15, 5))
        
        # Figure DPI
        dpi_frame = ctk.CTkFrame(self.settings_frame)
        dpi_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(dpi_frame, text="Figure quality (DPI):").pack(side="left", padx=5)
        self.dpi_var = tk.IntVar(value=self.settings.figure_dpi)
        dpi_menu = ctk.CTkOptionMenu(
            dpi_frame,
            variable=self.dpi_var,
            values=["72", "100", "150", "200", "300"]
        )
        dpi_menu.pack(side="right", padx=5)
        
        # Figure style
        style_frame = ctk.CTkFrame(self.settings_frame)
        style_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(style_frame, text="Figure style:").pack(side="left", padx=5)
        self.style_var = tk.StringVar(value=self.settings.figure_style)
        style_menu = ctk.CTkOptionMenu(
            style_frame,
            variable=self.style_var,
            values=["dark_background", "default", "seaborn", "ggplot", "bmh"]
        )
        style_menu.pack(side="right", padx=5)
        
        # Auto refresh
        self.auto_refresh_var = tk.BooleanVar(value=self.settings.auto_refresh)
        refresh_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Auto-refresh visualizations on filter changes",
            variable=self.auto_refresh_var
        )
        refresh_checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Show performance stats
        self.perf_stats_var = tk.BooleanVar(value=self.settings.show_performance_stats)
        perf_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Show performance statistics",
            variable=self.perf_stats_var
        )
        perf_checkbox.pack(anchor="w", padx=10, pady=2)
    
    def apply_settings(self):
        """Apply the current settings"""
        # Update settings object based on type
        if self.settings_type == "timeline":
            self.settings.timeline_show_trend = self.trend_var.get()
            self.settings.timeline_show_markers = self.markers_var.get()
            self.settings.timeline_line_style = self.line_style_var.get()
            self.settings.timeline_color_scheme = self.timeline_color_var.get()
            self.settings.timeline_y_scale = self.y_scale_var.get()
            self.settings.timeline_grid = self.timeline_grid_var.get()
        
        elif self.settings_type == "map":
            self.settings.map_show_coastline = self.coastline_var.get()
            self.settings.map_track_width = self.track_width_var.get()
            self.settings.map_show_categories = self.map_categories_var.get()
            self.settings.map_show_markers = self.map_markers_var.get()
            self.settings.map_projection = self.projection_var.get()
        
        elif self.settings_type == "analysis":
            self.settings.analysis_chart_types["category_dist"] = self.cat_chart_var.get()
            self.settings.analysis_chart_types["intensity_trends"] = self.int_chart_var.get()
            self.settings.analysis_chart_types["monthly_activity"] = self.monthly_chart_var.get()
            self.settings.analysis_color_scheme = self.analysis_color_var.get()
            self.settings.analysis_normalize_data = self.normalize_var.get()
            self.settings.analysis_show_statistics = self.stats_var.get()
            self.settings.analysis_show_grid = self.analysis_grid_var.get()
        
        # Update general settings
        self.settings.figure_dpi = int(self.dpi_var.get())
        self.settings.figure_style = self.style_var.get()
        self.settings.auto_refresh = self.auto_refresh_var.get()
        self.settings.show_performance_stats = self.perf_stats_var.get()
        
        # Call callback if provided
        if self.callback:
            self.callback(self.settings)
        
        self.close_window()
    
    def reset_settings(self):
        """Reset settings to defaults"""
        default_settings = VisualizationSettings()
        
        # Update UI elements based on type
        if self.settings_type == "timeline":
            self.trend_var.set(default_settings.timeline_show_trend)
            self.markers_var.set(default_settings.timeline_show_markers)
            self.line_style_var.set(default_settings.timeline_line_style)
            self.timeline_color_var.set(default_settings.timeline_color_scheme)
            self.y_scale_var.set(default_settings.timeline_y_scale)
            self.timeline_grid_var.set(default_settings.timeline_grid)
        
        elif self.settings_type == "map":
            self.coastline_var.set(default_settings.map_show_coastline)
            self.track_width_var.set(default_settings.map_track_width)
            self.map_categories_var.set(default_settings.map_show_categories)
            self.map_markers_var.set(default_settings.map_show_markers)
            self.projection_var.set(default_settings.map_projection)
        
        elif self.settings_type == "analysis":
            self.cat_chart_var.set(default_settings.analysis_chart_types["category_dist"])
            self.int_chart_var.set(default_settings.analysis_chart_types["intensity_trends"])
            self.monthly_chart_var.set(default_settings.analysis_chart_types["monthly_activity"])
            self.analysis_color_var.set(default_settings.analysis_color_scheme)
            self.normalize_var.set(default_settings.analysis_normalize_data)
            self.stats_var.set(default_settings.analysis_show_statistics)
            self.analysis_grid_var.set(default_settings.analysis_show_grid)
        
        # Update general settings
        self.dpi_var.set(default_settings.figure_dpi)
        self.style_var.set(default_settings.figure_style)
        self.auto_refresh_var.set(default_settings.auto_refresh)
        self.perf_stats_var.set(default_settings.show_performance_stats)
    
    def close_window(self):
        """Close the settings window"""
        self.window.grab_release()
        self.window.destroy()

class SettingsManager:
    """Manager for visualization settings across the application"""
    
    def __init__(self, settings_file: str = "dashboard_settings.json"):
        self.settings_file = Path(settings_file)
        self.settings = VisualizationSettings()
        self.callbacks: Dict[str, Callable] = {}
        
        # Load saved settings
        self.load_settings()
    
    def register_callback(self, visualization_type: str, callback: Callable):
        """Register a callback for when settings change"""
        self.callbacks[visualization_type] = callback
    
    def open_settings_popup(self, parent, visualization_type: str):
        """Open settings popup for a specific visualization type"""
        def on_settings_change(updated_settings):
            self.settings = updated_settings
            self.save_settings()
            
            # Call registered callback
            if visualization_type in self.callbacks:
                self.callbacks[visualization_type](self.settings)
        
        popup = SettingsPopupWindow(
            parent=parent,
            title=f"{visualization_type.title()} Visualization",
            settings=self.settings,
            settings_type=visualization_type,
            callback=on_settings_change
        )
    
    def save_settings(self):
        """Save settings to file"""
        try:
            settings_dict = {
                # Timeline settings
                'timeline_show_trend': self.settings.timeline_show_trend,
                'timeline_show_markers': self.settings.timeline_show_markers,
                'timeline_line_style': self.settings.timeline_line_style,
                'timeline_color_scheme': self.settings.timeline_color_scheme,
                'timeline_y_scale': self.settings.timeline_y_scale,
                'timeline_grid': self.settings.timeline_grid,
                
                # Map settings
                'map_show_coastline': self.settings.map_show_coastline,
                'map_track_width': self.settings.map_track_width,
                'map_show_categories': self.settings.map_show_categories,
                'map_show_markers': self.settings.map_show_markers,
                'map_projection': self.settings.map_projection,
                'map_zoom_level': self.settings.map_zoom_level,
                
                # Analysis settings
                'analysis_show_grid': self.settings.analysis_show_grid,
                'analysis_color_scheme': self.settings.analysis_color_scheme,
                'analysis_chart_types': self.settings.analysis_chart_types,
                'analysis_normalize_data': self.settings.analysis_normalize_data,
                'analysis_show_statistics': self.settings.analysis_show_statistics,
                
                # General settings
                'figure_dpi': self.settings.figure_dpi,
                'figure_style': self.settings.figure_style,
                'auto_refresh': self.settings.auto_refresh,
                'show_performance_stats': self.settings.show_performance_stats
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_dict, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Failed to save settings: {e}")
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings_dict = json.load(f)
                
                # Update settings object
                for key, value in settings_dict.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                        
                print("✅ Settings loaded from file")
            else:
                print("ℹ️  Using default settings (no saved settings found)")
                
        except Exception as e:
            print(f"⚠️  Failed to load settings: {e}")
            print("ℹ️  Using default settings")

def create_settings_gear_button(parent_frame, settings_manager: SettingsManager, 
                               visualization_type: str) -> ctk.CTkButton:
    """Create a gear icon settings button for a visualization"""
    
    gear_button = ctk.CTkButton(
        parent_frame,
        text="⚙️",
        width=35,
        height=35,
        font=ctk.CTkFont(size=16),
        command=lambda: settings_manager.open_settings_popup(
            parent_frame.winfo_toplevel(), 
            visualization_type
        )
    )
    
    return gear_button