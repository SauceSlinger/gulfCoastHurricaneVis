"""
Gulf Coast Hurricane Visualization Dashboard
A beautiful customTkinter application for visualizing hurricane data
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import webbrowser
import tempfile
import os
try:
    from tkinter import Frame
    import subprocess
    import platform
except ImportError:
    pass

# Import our custom modules
from data_processor import HurricaneDataProcessor
from visualizations import HurricaneVisualizations

# Try to import database-related modules, fallback gracefully
try:
    from view_manager import ViewType, CacheStatus, PersistentViewManager, FilterState
    DATABASE_FEATURES_AVAILABLE = True
except ImportError:
    # Define fallback classes for when database features aren't available
    class ViewType:
        TIMELINE = "timeline"
        MAP = "map" 
        ANALYSIS = "analysis"
    
    class CacheStatus:
        READY = "ready"
        LOADING = "loading"
        NOT_FOUND = "not_found"
    
    DATABASE_FEATURES_AVAILABLE = False
    print("⚠️  Database features not available, using CSV-only mode")

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class HurricaneDashboard:
    def __init__(self):
        # Initialize main window
        self.root = ctk.CTk()
        self.root.title("Gulf Coast Hurricane Data Visualization Dashboard")
        self.root.geometry("1800x1000")
        self.root.minsize(1400, 800)
        
        # Initialize loading variables
        self.loading_window = None
        self.progress_var = None
        self.progress_bar = None
        self.progress_label = None
        
        # Initialize storm selector variables early
        self.selected_storms = []
        self.storm_search_var = tk.StringVar()
        self.all_storms = []
        self.filtered_storms = []
        
        # Show loading window and initialize in background
        self.show_loading_window()
        self.root.after(100, self.initialize_dashboard)
    
    def show_loading_window(self):
        """Create and show loading progress window"""
        # Create loading window
        self.loading_window = ctk.CTkToplevel(self.root)
        self.loading_window.title("Loading Hurricane Dashboard")
        self.loading_window.geometry("400x200")
        self.loading_window.resizable(False, False)
        
        # Center the loading window
        self.loading_window.transient(self.root)
        self.loading_window.grab_set()
        
        # Loading content
        loading_frame = ctk.CTkFrame(self.loading_window)
        loading_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            loading_frame,
            text="🌀 Initializing Hurricane Dashboard",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            loading_frame,
            variable=self.progress_var,
            width=300,
            height=20
        )
        self.progress_bar.pack(pady=10)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            loading_frame,
            text="Preparing to load data...",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)
        
        # Set initial progress
        self.progress_var.set(0.0)
        self.root.update()
    
    def update_progress(self, value, message=""):
        """Update loading progress"""
        if self.progress_var and self.progress_label:
            self.progress_var.set(value)
            if message:
                self.progress_label.configure(text=message)
            self.root.update()
    
    def initialize_dashboard(self):
        """Initialize dashboard components with progress updates"""
        try:
            # Step 1: Initialize data processor
            self.update_progress(0.1, "Loading hurricane data processor...")
            self.data_processor = HurricaneDataProcessor()
            
            # Step 2: Load and process Gulf Coast data  
            self.update_progress(0.3, "Processing Gulf Coast hurricane data...")
            # Force data loading to show progress
            if hasattr(self.data_processor, 'gulf_coast_data'):
                pass  # Data already loaded
            
            # Step 3: Initialize visualizations
            self.update_progress(0.5, "Initializing visualization engine...")
            self.visualizer = HurricaneVisualizations()
            
            # Step 3.5: Initialize persistent view manager (if available)
            if DATABASE_FEATURES_AVAILABLE:
                self.update_progress(0.55, "Setting up persistent view system...")
                try:
                    from view_manager import PersistentViewManager
                    self.view_manager = PersistentViewManager(self.data_processor, self.visualizer)
                    
                    # Register view update callbacks
                    self.view_manager.register_update_callback(ViewType.TIMELINE, self._on_timeline_cache_ready)
                    self.view_manager.register_update_callback(ViewType.MAP, self._on_map_cache_ready)
                    self.view_manager.register_update_callback(ViewType.ANALYSIS, self._on_analysis_cache_ready)
                    print("✅ Persistent view manager initialized")
                except Exception as e:
                    print(f"⚠️  View manager initialization failed: {e}")
                    self.view_manager = None
            else:
                self.update_progress(0.55, "Using standard visualization mode...")
                self.view_manager = None
                print("ℹ️  Using CSV-only mode (no persistent views)")
            
            # Step 4: Create UI layout
            self.update_progress(0.6, "Creating dashboard layout...")
            self.create_layout()
            
            # Step 5: Create sidebar
            self.update_progress(0.7, "Setting up control panel...")
            self.create_sidebar()
            
            # Step 6: Create main content
            self.update_progress(0.8, "Building visualization panels...")
            self.create_main_content()
            
            # Step 7: Create storm selector panel
            self.update_progress(0.85, "Setting up storm selector...")
            self.create_storm_selector()
            
            # Step 8: Create status bar
            self.update_progress(0.9, "Finalizing interface...")
            self.create_status_bar()
            
            # Step 8: Initialize data and complete
            self.update_progress(0.95, "Loading initial dataset...")
            self.current_data = None
            self.current_viz_type = "Timeline Overview"
            
            # Set up storm search callback now that UI is ready
            self.storm_search_var.trace_add("write", self.on_storm_search)
            
            # Update with default view
            self.update_dashboard()
            
            # Complete loading
            self.update_progress(1.0, "Dashboard ready!")
            self.root.after(500, self.close_loading_window)
            
        except Exception as e:
            self.update_progress(0.0, f"Error: {str(e)}")
            print(f"Dashboard initialization error: {e}")
            self.root.after(2000, self.close_loading_window)
    
    def close_loading_window(self):
        """Close loading window and show main dashboard"""
        if self.loading_window:
            self.loading_window.destroy()
            self.loading_window = None
        
        # Make sure main window is visible and focused
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def get_filtered_data(self):
        """Get data filtered by current UI settings"""
        if not self.data_processor or self.data_processor.gulf_coast_data is None:
            return pd.DataFrame()
        
        # Determine which dataset to use based on scope
        scope = self.scope_var.get()
        dataset_type = "full_atlantic" if scope == "Full Atlantic Basin" else "gulf_coast"
        
        # Get filter values from UI
        start_year = int(self.year_start_var.get()) if self.year_start_var.get().isdigit() else 1975
        end_year = int(self.year_end_var.get()) if self.year_end_var.get().isdigit() else 2021
        
        # Get selected categories
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
        
        # Get season selection
        season_type = self.season_var.get()
        
        # Apply filters step by step
        filtered_data = self.data_processor.filter_by_year_range(start_year, end_year, dataset_type)
        filtered_data = self.data_processor.filter_by_categories(selected_categories, filtered_data)
        filtered_data = self.data_processor.filter_by_season(season_type, filtered_data)
        
        return filtered_data
    
    def create_layout(self):
        """Create the main layout structure with storm selector panel"""
        # Configure grid weights for three-panel layout
        self.root.grid_columnconfigure(1, weight=1)  # Main content expands
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main frames
        # Left sidebar - Controls
        self.sidebar_frame = ctk.CTkFrame(self.root, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.grid_propagate(False)
        
        # Center main content
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Right storm selector panel
        self.storm_selector_frame = ctk.CTkFrame(self.root, width=320, corner_radius=0)
        self.storm_selector_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=0, pady=0)
        self.storm_selector_frame.grid_propagate(False)
        
        # Status bar spans all columns
        self.status_frame = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.status_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=(0,10))
        self.status_frame.grid_propagate(False)
    
    def create_sidebar(self):
        """Create the sidebar with controls"""
        # Title
        title_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Gulf Coast Hurricane\nVisualization Dashboard", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1f538d", "#14375e")
        )
        title_label.pack(pady=(20, 30), padx=20)
        
        # Year Range Filter
        year_frame = ctk.CTkFrame(self.sidebar_frame)
        year_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(year_frame, text="Year Range", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.year_start_var = tk.StringVar(value="1975")
        self.year_end_var = tk.StringVar(value="2021")
        
        year_start_frame = ctk.CTkFrame(year_frame)
        year_start_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(year_start_frame, text="From:").pack(side="left", padx=5)
        self.year_start_entry = ctk.CTkEntry(year_start_frame, textvariable=self.year_start_var, width=80)
        self.year_start_entry.pack(side="right", padx=5)
        
        year_end_frame = ctk.CTkFrame(year_frame)
        year_end_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(year_end_frame, text="To:").pack(side="left", padx=5)
        self.year_end_entry = ctk.CTkEntry(year_end_frame, textvariable=self.year_end_var, width=80)
        self.year_end_entry.pack(side="right", padx=5)
        
        # Category Filter
        category_frame = ctk.CTkFrame(self.sidebar_frame)
        category_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(category_frame, text="Hurricane Category", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.category_vars = {}
        categories = ["1", "2", "3", "4", "5", "All Storms"]
        for cat in categories:
            var = tk.BooleanVar(value=True)
            self.category_vars[cat] = var
            checkbox = ctk.CTkCheckBox(category_frame, text=f"Category {cat}" if cat != "All Storms" else cat, variable=var)
            checkbox.pack(anchor="w", padx=10, pady=2)
        
        # Season Filter
        season_frame = ctk.CTkFrame(self.sidebar_frame)
        season_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(season_frame, text="Hurricane Season", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.season_var = tk.StringVar(value="All Year")
        season_options = ["All Year", "Peak Season (Aug-Oct)", "Early Season (Jun-Jul)", "Late Season (Nov)"]
        season_menu = ctk.CTkOptionMenu(season_frame, variable=self.season_var, values=season_options)
        season_menu.pack(padx=10, pady=5, fill="x")
        
        # Visualization Type
        viz_frame = ctk.CTkFrame(self.sidebar_frame)
        viz_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(viz_frame, text="Visualization Type", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.viz_var = tk.StringVar(value="Timeline Overview")
        viz_options = ["Timeline Overview", "Geographic Map", "Impact Analysis", "Storm Tracks", "Statistical Summary"]
        viz_menu = ctk.CTkOptionMenu(viz_frame, variable=self.viz_var, values=viz_options, command=self.on_viz_change)
        viz_menu.pack(padx=10, pady=5, fill="x")
        
        # Geographic Scope (new)
        scope_frame = ctk.CTkFrame(self.sidebar_frame)
        scope_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(scope_frame, text="Geographic Scope", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.scope_var = tk.StringVar(value="Full Atlantic Basin")
        scope_options = ["Gulf Coast Focus", "Full Atlantic Basin"]
        scope_menu = ctk.CTkOptionMenu(scope_frame, variable=self.scope_var, values=scope_options, command=self.on_scope_change)
        scope_menu.pack(padx=10, pady=5, fill="x")
        
        # Update Button
        update_button = ctk.CTkButton(
            self.sidebar_frame, 
            text="Update Dashboard", 
            command=self.update_dashboard,
            height=40,
            font=ctk.CTkFont(weight="bold")
        )
        update_button.pack(pady=30, padx=20, fill="x")
        
        # Info Panel
        info_frame = ctk.CTkFrame(self.sidebar_frame)
        info_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        ctk.CTkLabel(info_frame, text="Dataset Information", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.info_text = ctk.CTkTextbox(info_frame, height=150, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.update_info_panel()
    
    def create_main_content(self):
        """Create the main content area"""
        # Header
        header_frame = ctk.CTkFrame(self.main_frame, height=60)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.grid_propagate(False)
        
        self.header_label = ctk.CTkLabel(
            header_frame, 
            text="Gulf Coast Hurricane Timeline Overview", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.header_label.pack(pady=15)
        
        # Content notebook for multiple views
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.timeline_frame = ttk.Frame(self.notebook)
        self.map_frame = ttk.Frame(self.notebook)
        self.analysis_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.timeline_frame, text="Timeline View")
        self.notebook.add(self.map_frame, text="Geographic View")
        self.notebook.add(self.analysis_frame, text="Analysis View")
        
        # Placeholder content
        self.create_timeline_content()
        self.create_map_content()
        self.create_analysis_content()
    
    def create_timeline_content(self):
        """Create timeline visualization content"""
        # Create a frame for the visualization
        self.timeline_content = ctk.CTkFrame(self.timeline_frame)
        self.timeline_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create control frame at the top
        control_frame = ctk.CTkFrame(self.timeline_content, height=60)
        control_frame.pack(fill="x", padx=10, pady=5)
        control_frame.pack_propagate(False)
        
        # Add button to generate visualization
        self.timeline_button = ctk.CTkButton(
            control_frame,
            text="Generate Timeline Visualization",
            command=lambda: self.generate_embedded_visualization("timeline"),
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.timeline_button.pack(side="left", padx=10, pady=10)
        
        # Add button to open in browser
        self.timeline_browser_button = ctk.CTkButton(
            control_frame,
            text="Open in Browser",
            command=lambda: self.show_visualization("timeline"),
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.timeline_browser_button.pack(side="left", padx=5, pady=10)
        
        # Status label
        self.timeline_status = ctk.CTkLabel(
            control_frame,
            text="Ready to generate chart",
            font=ctk.CTkFont(size=12)
        )
        self.timeline_status.pack(side="right", padx=10, pady=15)
        
        # Create visualization display area
        self.timeline_display = ctk.CTkScrollableFrame(self.timeline_content)
        self.timeline_display.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial placeholder
        self.create_timeline_placeholder()
    
    def create_map_content(self):
        """Create map visualization content"""
        # Create a frame for the visualization
        self.map_content = ctk.CTkFrame(self.map_frame)
        self.map_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create control frame at the top
        control_frame = ctk.CTkFrame(self.map_content, height=60)
        control_frame.pack(fill="x", padx=10, pady=5)
        control_frame.pack_propagate(False)
        
        # Add button to generate visualization
        self.map_button = ctk.CTkButton(
            control_frame,
            text="Generate Storm Track Map",
            command=lambda: self.generate_embedded_visualization("map"),
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.map_button.pack(side="left", padx=10, pady=10)
        
        # Add button to open in browser
        self.map_browser_button = ctk.CTkButton(
            control_frame,
            text="Open in Browser",
            command=lambda: self.show_visualization("map"),
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.map_browser_button.pack(side="left", padx=5, pady=10)
        
        # Status label
        self.map_status = ctk.CTkLabel(
            control_frame,
            text="Ready to generate map",
            font=ctk.CTkFont(size=12)
        )
        self.map_status.pack(side="right", padx=10, pady=15)
        
        # Create visualization display area
        self.map_display = ctk.CTkScrollableFrame(self.map_content)
        self.map_display.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial placeholder
        self.create_map_placeholder()
    
    def create_analysis_content(self):
        """Create analysis visualization content"""
        # Create a frame for the visualization
        self.analysis_content = ctk.CTkFrame(self.analysis_frame)
        self.analysis_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create control frame at the top
        control_frame = ctk.CTkFrame(self.analysis_content, height=60)
        control_frame.pack(fill="x", padx=10, pady=5)
        control_frame.pack_propagate(False)
        
        # Add button to generate visualization
        self.analysis_button = ctk.CTkButton(
            control_frame,
            text="Generate Impact Analysis",
            command=lambda: self.generate_embedded_visualization("analysis"),
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.analysis_button.pack(side="left", padx=10, pady=10)
        
        # Add button to open in browser
        self.analysis_browser_button = ctk.CTkButton(
            control_frame,
            text="Open in Browser",
            command=lambda: self.show_visualization("analysis"),
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.analysis_browser_button.pack(side="left", padx=5, pady=10)
        
        # Status label
        self.analysis_status = ctk.CTkLabel(
            control_frame,
            text="Ready to generate analysis",
            font=ctk.CTkFont(size=12)
        )
        self.analysis_status.pack(side="right", padx=10, pady=15)
        
        # Create visualization display area
        self.analysis_display = ctk.CTkScrollableFrame(self.analysis_content)
        self.analysis_display.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial placeholder
        self.create_analysis_placeholder()
    
    def create_status_bar(self):
        """Create status bar with progress indicator"""
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Ready • Hurricane data loaded • Dashboard initialized",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Progress bar (initially hidden)
        self.status_progress_var = tk.DoubleVar()
        self.status_progress_bar = ctk.CTkProgressBar(
            self.status_frame,
            variable=self.status_progress_var,
            width=200,
            height=8
        )
        self.status_progress_bar.pack(side="left", padx=10, pady=5)
        self.status_progress_bar.pack_forget()  # Hide initially
        
        self.last_updated_label = ctk.CTkLabel(
            self.status_frame, 
            text=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=ctk.CTkFont(size=12)
        )
        self.last_updated_label.pack(side="right", padx=10, pady=5)
    
    def show_status_progress(self):
        """Show progress bar in status bar"""
        self.status_progress_bar.pack(side="left", padx=10, pady=5, before=self.last_updated_label)
        self.status_progress_var.set(0.0)
    
    def hide_status_progress(self):
        """Hide progress bar in status bar"""
        self.status_progress_bar.pack_forget()
    
    def update_status_progress(self, value):
        """Update status bar progress"""
        if self.status_progress_var:
            self.status_progress_var.set(value)
            self.root.update_idletasks()
    
    def create_storm_selector(self):
        """Create the storm selector panel with search and list"""
        # Title
        title_label = ctk.CTkLabel(
            self.storm_selector_frame,
            text="🌀 Storm Selector",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#14375e")
        )
        title_label.pack(pady=(15, 10), padx=15)
        
        # Search bar frame
        search_frame = ctk.CTkFrame(self.storm_selector_frame)
        search_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            search_frame,
            text="🔍 Search Storms:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        self.storm_search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Type storm name...",
            textvariable=self.storm_search_var,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.storm_search_entry.pack(fill="x", padx=10, pady=5)
        
        # Clear search button
        clear_button = ctk.CTkButton(
            search_frame,
            text="Clear Search",
            command=self.clear_storm_search,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        clear_button.pack(pady=(0, 5), padx=10)
        
        # Storm list frame
        list_frame = ctk.CTkFrame(self.storm_selector_frame)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        ctk.CTkLabel(
            list_frame,
            text="📋 Available Storms:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Scrollable storm list
        self.storm_list_frame = ctk.CTkScrollableFrame(list_frame, height=400)
        self.storm_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Selection info frame
        selection_frame = ctk.CTkFrame(self.storm_selector_frame)
        selection_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            selection_frame,
            text="✅ Selected Storms:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        self.selection_label = ctk.CTkLabel(
            selection_frame,
            text="None selected",
            font=ctk.CTkFont(size=11),
            wraplength=280
        )
        self.selection_label.pack(anchor="w", padx=10, pady=5)
        
        # Action buttons
        button_frame = ctk.CTkFrame(self.storm_selector_frame)
        button_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        highlight_button = ctk.CTkButton(
            button_frame,
            text="🎯 Highlight Selected",
            command=self.highlight_selected_storms,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        highlight_button.pack(fill="x", padx=10, pady=5)
        
        clear_selection_button = ctk.CTkButton(
            button_frame,
            text="🚫 Clear Selection",
            command=self.clear_storm_selection,
            height=30,
            font=ctk.CTkFont(size=11)
        )
        clear_selection_button.pack(fill="x", padx=10, pady=2)
        
        # Initialize storm list
        self.populate_storm_list()
    
    def populate_storm_list(self):
        """Populate the storm list with available storms"""
        try:
            # Get current filtered data
            current_data = self.get_filtered_data()
            
            if current_data is not None and len(current_data) > 0:
                # Get unique storms with their details
                storms = current_data.groupby(['name', 'year']).agg({
                    'category': 'max',
                    'wind': 'max',
                    'pressure': 'min',
                    'lat': ['min', 'max'],
                    'long': ['min', 'max']
                }).reset_index()
                
                # Flatten column names
                storms.columns = ['name', 'year', 'max_category', 'max_wind', 'min_pressure', 'min_lat', 'max_lat', 'min_long', 'max_long']
                
                # Sort storms by year (descending) then by max wind speed
                storms = storms.sort_values(['year', 'max_wind'], ascending=[False, False])
                
                self.all_storms = storms.to_dict('records')
                self.filtered_storms = self.all_storms.copy()
                
                # Update the display
                self.update_storm_list_display()
            else:
                self.all_storms = []
                self.filtered_storms = []
                self.update_storm_list_display()
                
        except Exception as e:
            print(f"Error populating storm list: {e}")
            self.all_storms = []
            self.filtered_storms = []
    
    def update_storm_list_display(self):
        """Update the visual display of the storm list"""
        # Clear existing widgets
        for widget in self.storm_list_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_storms:
            no_storms_label = ctk.CTkLabel(
                self.storm_list_frame,
                text="No storms match current filters",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_storms_label.pack(pady=20)
            return
        
        # Create storm entries
        for i, storm in enumerate(self.filtered_storms):
            self.create_storm_entry(storm, i)
    
    def create_storm_entry(self, storm, index):
        """Create a single storm entry in the list"""
        # Storm frame
        storm_frame = ctk.CTkFrame(self.storm_list_frame)
        storm_frame.pack(fill="x", padx=5, pady=2)
        
        # Create storm identifier
        storm_id = f"{storm['name']}_{storm['year']}"
        
        # Check if storm is selected
        is_selected = storm_id in self.selected_storms
        
        # Storm button (clickable)
        storm_button = ctk.CTkButton(
            storm_frame,
            text="",
            command=lambda s=storm_id: self.toggle_storm_selection(s),
            height=60,
            corner_radius=5,
            hover_color=("#3a7ebf", "#1f538d"),
            fg_color=("#1f538d", "#14375e") if is_selected else ("gray75", "gray25")
        )
        storm_button.pack(fill="x", padx=5, pady=2)
        
        # Storm info label (overlay on button)
        max_wind = storm.get('max_wind', 0)
        max_category = storm.get('max_category', 'N/A')
        
        # Format storm info
        storm_text = f"🌀 {storm['name']} ({storm['year']})\n"
        storm_text += f"Category {max_category} • {max_wind:.0f} mph"
        
        if storm.get('min_pressure'):
            storm_text += f" • {storm['min_pressure']:.0f} mb"
        
        info_label = ctk.CTkLabel(
            storm_button,
            text=storm_text,
            font=ctk.CTkFont(size=10),
            justify="left"
        )
        info_label.place(relx=0.05, rely=0.5, anchor="w")
        
        # Selection indicator
        if is_selected:
            indicator = ctk.CTkLabel(
                storm_button,
                text="✓",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="lime"
            )
            indicator.place(relx=0.95, rely=0.5, anchor="e")
    
    def on_storm_search(self, *args):
        """Handle storm search input"""
        search_text = self.storm_search_var.get().lower().strip()
        
        if not search_text:
            self.filtered_storms = self.all_storms.copy()
        else:
            self.filtered_storms = [
                storm for storm in self.all_storms
                if search_text in storm['name'].lower() or 
                   search_text in str(storm['year'])
            ]
        
        self.update_storm_list_display()
    
    def clear_storm_search(self):
        """Clear the storm search"""
        self.storm_search_var.set("")
    
    def toggle_storm_selection(self, storm_id):
        """Toggle selection of a storm"""
        if storm_id in self.selected_storms:
            self.selected_storms.remove(storm_id)
        else:
            self.selected_storms.append(storm_id)
        
        # Update display
        self.update_storm_list_display()
        self.update_selection_display()
        
        # Update status
        storm_name = storm_id.split('_')[0]
        storm_year = storm_id.split('_')[1]
        action = "Selected" if storm_id in self.selected_storms else "Deselected"
        self.update_status(f"{action} storm: {storm_name} ({storm_year})")
    
    def update_selection_display(self):
        """Update the selection display label"""
        if not self.selected_storms:
            self.selection_label.configure(text="None selected")
        else:
            selected_names = []
            for storm_id in self.selected_storms:
                name, year = storm_id.split('_')
                selected_names.append(f"{name} ({year})")
            
            if len(selected_names) <= 3:
                display_text = ", ".join(selected_names)
            else:
                display_text = f"{', '.join(selected_names[:3])}... (+{len(selected_names) - 3} more)"
            
            self.selection_label.configure(text=display_text)
    
    def clear_storm_selection(self):
        """Clear all storm selections"""
        self.selected_storms.clear()
        self.update_storm_list_display()
        self.update_selection_display()
        self.update_status("Cleared storm selection")
    
    def highlight_selected_storms(self):
        """Highlight selected storms in current visualization"""
        if not self.selected_storms:
            self.update_status("No storms selected for highlighting")
            return
        
        # Re-generate current visualization with highlighting
        current_tab = self.notebook.index(self.notebook.select())
        
        if current_tab == 0:  # Timeline
            self.generate_timeline_with_highlight()
        elif current_tab == 1:  # Map
            self.generate_map_with_highlight()
        elif current_tab == 2:  # Analysis
            self.generate_analysis_with_highlight()
        
        storm_count = len(self.selected_storms)
        self.update_status(f"Highlighting {storm_count} selected storm(s)")
    
    def generate_timeline_with_highlight(self):
        """Generate timeline with selected storms highlighted"""
        try:
            self.show_status_progress()
            self.update_status_progress(0.1)
            self.update_status("Generating highlighted timeline...")
            
            # Get filtered data
            filtered_data = self.get_filtered_data()
            
            if len(filtered_data) == 0:
                self.hide_status_progress()
                return
            
            # Clear existing content
            for widget in self.timeline_display.winfo_children():
                widget.destroy()
            
            self.update_status_progress(0.3)
            
            # Generate annual summary with highlighting
            annual_data = self.data_processor.get_annual_storm_summary(filtered_data)
            
            self.update_status_progress(0.6)
            
            # Create visualization with highlighting
            fig = self.visualizer.create_timeline_overview_with_highlight(
                annual_data, self.selected_storms
            )
            
            self.update_status_progress(0.8)
            
            # Display
            self.display_plotly_as_image(fig, self.timeline_display, "timeline_highlighted")
            self.add_timeline_summary(annual_data)
            
            self.update_status_progress(1.0)
            self.timeline_status.configure(text="Timeline with highlights generated")
            self.update_status("Timeline highlighting complete")
            
            self.root.after(1000, self.hide_status_progress)
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error highlighting timeline: {str(e)}")
    
    def generate_map_with_highlight(self):
        """Generate map with selected storms highlighted"""
        try:
            self.show_status_progress()
            self.update_status_progress(0.1)
            self.update_status("Generating highlighted map...")
            
            # Get filtered data
            filtered_data = self.get_filtered_data()
            
            if len(filtered_data) == 0:
                self.hide_status_progress()
                return
            
            # Clear existing content
            for widget in self.map_display.winfo_children():
                widget.destroy()
            
            self.update_status_progress(0.3)
            
            # Get storm tracks with highlighting info
            scope = self.scope_var.get()
            map_scope = "atlantic" if scope == "Full Atlantic Basin" else "gulf"
            storm_limit = 20 if scope == "Full Atlantic Basin" else 10
            
            storm_tracks = self.data_processor.get_storm_tracks(filtered_data, limit=storm_limit)
            
            self.update_status_progress(0.6)
            
            # Create visualization with highlighting
            title = f"Hurricane Tracks - {scope} (Highlighted)"
            fig = self.visualizer.create_storm_track_map_with_highlight(
                storm_tracks, self.selected_storms, title=title, map_scope=map_scope
            )
            
            self.update_status_progress(0.8)
            
            # Display
            self.display_plotly_as_image(fig, self.map_display, "map_highlighted")
            self.add_map_summary(storm_tracks, scope)
            
            self.update_status_progress(1.0)
            self.map_status.configure(text="Map with highlights generated")
            self.update_status("Map highlighting complete")
            
            self.root.after(1000, self.hide_status_progress)
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error highlighting map: {str(e)}")
    
    def generate_analysis_with_highlight(self):
        """Generate analysis with selected storms highlighted"""
        try:
            self.show_status_progress()
            self.update_status_progress(0.1)
            self.update_status("Generating highlighted analysis...")
            
            # For now, just regenerate normal analysis
            # Can be enhanced later with specific highlighting
            self.generate_analysis_embedded(self.get_filtered_data())
            
            self.update_status("Analysis highlighting complete (feature coming soon)")
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error highlighting analysis: {str(e)}")
    
    def update_info_panel(self):
        """Update the information panel with current data stats"""
        if self.data_processor and self.data_processor.gulf_coast_data is not None:
            # Get current scope
            scope = self.scope_var.get()
            
            if scope == "Full Atlantic Basin" and self.data_processor.full_atlantic_data is not None:
                # Use full Atlantic data
                current_dataset = self.data_processor.full_atlantic_data
                data_description = "Full Atlantic Basin Hurricane Data"
                coverage_description = "Complete Atlantic hurricane tracking from Africa to the Americas"
            else:
                # Use Gulf Coast data
                current_dataset = self.data_processor.gulf_coast_data
                data_description = "Gulf Coast Hurricane Data"
                coverage_description = "Texas to Florida coastline impacts"
            
            # Calculate statistics
            unique_storms = current_dataset.groupby(['name', 'year']).size().count()
            year_range = (current_dataset['year'].min(), current_dataset['year'].max())
            categories = sorted([cat for cat in current_dataset['category'].dropna().unique() if not pd.isna(cat)])
            
            stats = f"""{data_description}:
Total Records: {len(current_dataset):,}
Year Range: {year_range[0]}-{year_range[1]}
Unique Storms: {unique_storms}
Categories: {', '.join(map(str, categories))}

Geographic Coverage: {coverage_description}
Latitude: {current_dataset['lat'].min():.1f}° to {current_dataset['lat'].max():.1f}°N
Longitude: {current_dataset['long'].min():.1f}° to {current_dataset['long'].max():.1f}°W

Analysis Features:
- Storm tracking & paths
- Intensity analysis
- Seasonal patterns
- Impact projections
- Geographic scope selection"""
        else:
            stats = "Loading hurricane data..."
        
        self.info_text.delete("0.0", "end")
        self.info_text.insert("0.0", stats)
    
    def on_viz_change(self, value):
        """Handle visualization type change"""
        viz_titles = {
            "Timeline Overview": "Gulf Coast Hurricane Timeline Overview",
            "Geographic Map": "Hurricane Track Geographic Visualization", 
            "Impact Analysis": "Hurricane Impact Areas & Projections",
            "Storm Tracks": "Individual Storm Path Analysis",
            "Statistical Summary": "Hurricane Trends & Statistical Analysis"
        }
        
        self.header_label.configure(text=viz_titles.get(value, "Gulf Coast Hurricane Visualization"))
        self.update_status(f"Switched to {value} visualization")
    
    def on_scope_change(self, value):
        """Handle geographic scope change"""
        scope_info = {
            "Gulf Coast Focus": "Texas to Florida coastline hurricane impacts",
            "Full Atlantic Basin": "Complete Atlantic hurricane tracking from Africa to Americas"
        }
        
        self.update_status(f"Switched to {value} • {scope_info.get(value, '')}")
        # Update info panel to reflect new scope
        self.update_info_panel()
    
    def show_visualization(self, viz_type):
        """Show visualization in web browser"""
        # Show progress
        self.show_status_progress()
        self.update_status_progress(0.1)
        self.update_status(f"Preparing {viz_type} for browser...")
        
        try:
            # Get filtered data
            filtered_data = self.get_filtered_data()
            
            if filtered_data is None or len(filtered_data) == 0:
                self.hide_status_progress()
                self.update_status("No data available for current filters")
                return
            
            self.update_status_progress(0.3)
            self.update_status(f"Processing {viz_type} data...")
            
            # Generate appropriate visualization
            fig = None
            if viz_type == "timeline":
                annual_data = self.data_processor.get_annual_storm_summary(filtered_data)
                self.update_status_progress(0.6)
                self.update_status("Creating interactive timeline...")
                fig = self.visualizer.create_timeline_overview(annual_data)
                self.timeline_status.configure(text=f"Timeline generated with {len(annual_data)} years of data")
                
            elif viz_type == "map":
                scope = self.scope_var.get()
                map_scope = "atlantic" if scope == "Full Atlantic Basin" else "gulf"
                storm_limit = 25 if scope == "Full Atlantic Basin" else 15
                
                storm_tracks = self.data_processor.get_storm_tracks(filtered_data, limit=storm_limit)
                self.update_status_progress(0.6)
                self.update_status("Creating interactive map...")
                title = f"Hurricane Tracks - {scope}"
                fig = self.visualizer.create_storm_track_map(storm_tracks, title=title, map_scope=map_scope)
                self.map_status.configure(text=f"Map generated with {len(storm_tracks)} storm tracks")
                
            elif viz_type == "analysis":
                impact_stats = self.data_processor.get_impact_statistics(filtered_data)
                self.update_status_progress(0.6)
                self.update_status("Creating interactive analysis...")
                fig = self.visualizer.create_impact_heatmap(impact_stats)
                self.analysis_status.configure(text=f"Analysis generated for {impact_stats.get('total_storms', 0)} storms")
            
            if fig:
                self.update_status_progress(0.8)
                self.update_status("Exporting to HTML...")
                
                # Save to temporary HTML file and open in browser
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    fig.write_html(f.name, include_plotlyjs='inline')
                    
                    self.update_status_progress(1.0)
                    self.update_status("Opening in browser...")
                    webbrowser.open('file://' + os.path.realpath(f.name))
                
                self.update_status(f"{viz_type.title()} visualization opened in browser")
                # Hide progress after delay
                self.root.after(1500, self.hide_status_progress)
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error generating visualization: {str(e)}")
            print(f"Visualization error: {e}")
    
    def _on_timeline_cache_ready(self, cache):
        """Callback when timeline cache is ready"""
        if cache.status == CacheStatus.READY:
            self.root.after(0, lambda: self._update_timeline_view(cache))
    
    def _on_map_cache_ready(self, cache):
        """Callback when map cache is ready"""
        if cache.status == CacheStatus.READY:
            self.root.after(0, lambda: self._update_map_view(cache))
    
    def _on_analysis_cache_ready(self, cache):
        """Callback when analysis cache is ready"""
        if cache.status == CacheStatus.READY:
            self.root.after(0, lambda: self._update_analysis_view(cache))
    
    def _update_timeline_view(self, cache):
        """Update timeline view with cached data"""
        try:
            # Clear existing content
            for widget in self.timeline_display.winfo_children():
                widget.destroy()
            
            # Display cached visualization
            if cache.figure:
                self.display_plotly_as_image(cache.figure, self.timeline_display, "timeline_cached")
            
            # Add cached summary
            if cache.metadata:
                self._add_cached_timeline_summary(cache.metadata)
            
            self.timeline_status.configure(text="Timeline ready (cached)")
            self.update_status(f"Timeline updated from cache • {cache.metadata.get('storm_count', 0)} storms")
            
        except Exception as e:
            print(f"Error updating timeline view: {e}")
    
    def _update_map_view(self, cache):
        """Update map view with cached data"""
        try:
            # Clear existing content
            for widget in self.map_display.winfo_children():
                widget.destroy()
            
            # Display cached visualization
            if cache.figure:
                self.display_plotly_as_image(cache.figure, self.map_display, "map_cached")
            
            # Add cached summary
            if cache.metadata:
                self._add_cached_map_summary(cache.metadata)
            
            self.map_status.configure(text="Map ready (cached)")
            self.update_status(f"Map updated from cache • {cache.metadata.get('track_count', 0)} tracks")
            
        except Exception as e:
            print(f"Error updating map view: {e}")
    
    def _update_analysis_view(self, cache):
        """Update analysis view with cached data"""
        try:
            # Clear existing content
            for widget in self.analysis_display.winfo_children():
                widget.destroy()
            
            # Display cached visualization
            if cache.figure:
                self.display_plotly_as_image(cache.figure, self.analysis_display, "analysis_cached")
            
            # Add cached summary
            if cache.metadata:
                self._add_cached_analysis_summary(cache.metadata)
            
            self.analysis_status.configure(text="Analysis ready (cached)")
            self.update_status(f"Analysis updated from cache • {cache.metadata.get('total_storms', 0)} storms")
            
        except Exception as e:
            print(f"Error updating analysis view: {e}")
    
    def _add_cached_timeline_summary(self, metadata):
        """Add summary for cached timeline data"""
        summary_frame = ctk.CTkFrame(self.timeline_display)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            summary_frame,
            text="📈 Timeline Summary (Cached)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        stats_text = f"""Storm Count: {metadata.get('storm_count', 0)}
Year Range: {metadata.get('year_span', (0, 0))[0]} - {metadata.get('year_span', (0, 0))[1]}
Average Storms/Year: {metadata.get('avg_storms_per_year', 0):.1f}
Cache Status: Ready ✅"""
        
        stats_label = ctk.CTkLabel(
            summary_frame,
            text=stats_text.strip(),
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        stats_label.pack(pady=5)
    
    def _add_cached_map_summary(self, metadata):
        """Add summary for cached map data"""
        summary_frame = ctk.CTkFrame(self.map_display)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            summary_frame,
            text="🗺️ Map Summary (Cached)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        stats_text = f"""Storm Tracks: {metadata.get('track_count', 0)}
Geographic Scope: {metadata.get('geographic_scope', 'Unknown')}
Highlighted Storms: {metadata.get('highlighted_storms', 0)}
Cache Status: Ready ✅"""
        
        stats_label = ctk.CTkLabel(
            summary_frame,
            text=stats_text.strip(),
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        stats_label.pack(pady=5)
    
    def _add_cached_analysis_summary(self, metadata):
        """Add summary for cached analysis data"""
        summary_frame = ctk.CTkFrame(self.analysis_display)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            summary_frame,
            text="📊 Analysis Summary (Cached)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        stats_text = f"""Total Storms Analyzed: {metadata.get('total_storms', 0)}
Average Storms/Year: {metadata.get('avg_storms_per_year', 0):.1f}
Cache Status: Ready ✅"""
        
        stats_label = ctk.CTkLabel(
            summary_frame,
            text=stats_text.strip(),
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        stats_label.pack(pady=5)
    
    def update_dashboard(self):
        """Update the dashboard with current filter settings using view manager for instant responsiveness"""
        # Only show progress for significant updates (not initial load)
        if hasattr(self, 'status_progress_bar'):
            self.show_status_progress()
            self.update_status_progress(0.2)
        
        self.update_status("Updating dashboard...")
        
        try:
            # Update view manager with new filter state
            if hasattr(self, 'view_manager'):
                current_filter_state = self._get_current_filter_state()
                if hasattr(self, 'status_progress_bar'):
                    self.update_status_progress(0.4)
                
                # Check if we have cached views for current filters
                timeline_cache = self.view_manager.get_cached_view(ViewType.TIMELINE, current_filter_state)
                map_cache = self.view_manager.get_cached_view(ViewType.MAP, current_filter_state)
                analysis_cache = self.view_manager.get_cached_view(ViewType.ANALYSIS, current_filter_state)
                
                # Update instantly if cached data is available
                if timeline_cache and timeline_cache.status == CacheStatus.READY:
                    self._update_timeline_view(timeline_cache)
                if map_cache and map_cache.status == CacheStatus.READY:
                    self._update_map_view(map_cache)
                if analysis_cache and analysis_cache.status == CacheStatus.READY:
                    self._update_analysis_view(analysis_cache)
                
                # Trigger background refresh for views that aren't cached
                self.view_manager.update_filter_state(current_filter_state)
            
            # Get current filtered data (fallback for non-view-manager updates)
            if hasattr(self, 'status_progress_bar'):
                self.update_status_progress(0.6)
            self.current_data = self.get_filtered_data()
            
            # Update info panel
            if hasattr(self, 'status_progress_bar'):
                self.update_status_progress(0.75)
            self.update_info_panel()
            
            # Update storm list
            if hasattr(self, 'storm_list_frame'):
                if hasattr(self, 'status_progress_bar'):
                    self.update_status_progress(0.85)
                self.populate_storm_list()
            
            # Update timestamp
            if hasattr(self, 'last_updated_label'):
                self.last_updated_label.configure(text=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if hasattr(self, 'status_progress_bar'):
                self.update_status_progress(1.0)
            
            if self.current_data is not None and len(self.current_data) > 0:
                storm_count = self.current_data.groupby(['name', 'year']).size().count()
                cache_info = ""
                if hasattr(self, 'view_manager'):
                    cached_views = sum(1 for vt in ViewType if self.view_manager.get_cached_view(vt, current_filter_state))
                    cache_info = f" • {cached_views}/3 views cached"
                self.update_status(f"Dashboard updated • {storm_count} storms in current view{cache_info}")
            else:
                self.update_status("Dashboard updated • No storms match current filters")
            
            # Hide progress after delay if we showed it
            if hasattr(self, 'status_progress_bar'):
                self.root.after(800, self.hide_status_progress)
                
        except Exception as e:
            if hasattr(self, 'status_progress_bar'):
                self.hide_status_progress()
            self.update_status(f"Error updating dashboard: {str(e)}")
            print(f"Dashboard update error: {e}")
    
    def _get_current_filter_state(self):
        """Get current filter state for view manager"""
        try:
            # Extract filter values from UI components with safe defaults
            year_from = None
            year_to = None
            
            # Check if year entry widgets exist and have values
            if hasattr(self, 'year_start_var') and self.year_start_var.get().isdigit():
                year_from = int(self.year_start_var.get())
            elif hasattr(self, 'year_from_entry') and hasattr(self.year_from_entry, 'get'):
                year_text = self.year_from_entry.get()
                year_from = int(year_text) if year_text.isdigit() else None
            
            if hasattr(self, 'year_end_var') and self.year_end_var.get().isdigit():
                year_to = int(self.year_end_var.get())
            elif hasattr(self, 'year_to_entry') and hasattr(self.year_to_entry, 'get'):
                year_text = self.year_to_entry.get()
                year_to = int(year_text) if year_text.isdigit() else None
            
            # Get other filter values safely
            category_filter = None
            if hasattr(self, 'category_var'):
                category_filter = self.category_var.get()
            
            status_filter = None
            if hasattr(self, 'status_var'):
                status_filter = self.status_var.get()
            
            geographic_scope = "Gulf Coast Focus"
            if hasattr(self, 'scope_var'):
                geographic_scope = self.scope_var.get()
            
            season_type = "All Year"
            if hasattr(self, 'season_var'):
                season_type = self.season_var.get()
            
            # Get selected categories
            categories = []
            if hasattr(self, 'category_vars'):
                categories = [cat for cat, var in self.category_vars.items() if var.get()]
            
            # Create FilterState object with all available data
            return FilterState(
                start_year=year_from or 1975,
                end_year=year_to or 2021,
                categories=categories if categories else ["1", "2", "3", "4", "5", "All Storms"],
                season_type=season_type,
                geographic_scope=geographic_scope,
                selected_storms=list(self.selected_storms) if hasattr(self, 'selected_storms') else []
            )
            
        except Exception as e:
            print(f"Error getting filter state: {e}")
            return FilterState()  # Return default filter state on error
    
    def generate_embedded_visualization(self, viz_type):
        """Generate and embed visualization directly in the dashboard using view manager for caching"""
        self.update_status(f"Generating {viz_type} visualization...")
        
        # Check if we have a cached version available
        if hasattr(self, 'view_manager'):
            current_filter_state = self._get_current_filter_state()
            
            # Map viz_type string to ViewType enum
            view_type_map = {
                "timeline": ViewType.TIMELINE,
                "map": ViewType.MAP,
                "analysis": ViewType.ANALYSIS
            }
            
            if viz_type in view_type_map:
                view_type = view_type_map[viz_type]
                cached_view = self.view_manager.get_cached_view(view_type, current_filter_state)
                
                if cached_view and cached_view.status == CacheStatus.READY:
                    # Use cached version instantly
                    if viz_type == "timeline":
                        self._update_timeline_view(cached_view)
                    elif viz_type == "map":
                        self._update_map_view(cached_view)
                    elif viz_type == "analysis":
                        self._update_analysis_view(cached_view)
                    
                    self.update_status(f"{viz_type.title()} loaded from cache ⚡")
                    return
                
                # If not cached, trigger background generation and show placeholder
                self.view_manager.update_filter_state(current_filter_state)
                self.update_status(f"{viz_type.title()} generating in background...")
        
        # Fallback to traditional generation if no view manager or cache miss
        self.show_generation_progress(viz_type)
        
        try:
            # Get filtered data
            filtered_data = self.get_filtered_data()
            
            if len(filtered_data) == 0:
                self.update_status("No data available for current filters")
                return
            
            # Generate the appropriate visualization
            if viz_type == "timeline":
                self.generate_timeline_embedded(filtered_data)
            elif viz_type == "map":
                self.generate_map_embedded(filtered_data)
            elif viz_type == "analysis":
                self.generate_analysis_embedded(filtered_data)
                
        except Exception as e:
            self.update_status(f"Error generating {viz_type}: {str(e)}")
    
    def show_generation_progress(self, viz_type):
        """Show progress animation during visualization generation"""
        # Create a simple progress indicator in the status bar
        progress_messages = [
            f"🔄 Preparing {viz_type} data...",
            f"📊 Processing {viz_type} visualization...", 
            f"🎨 Rendering {viz_type} graphics...",
            f"✅ {viz_type.title()} visualization complete!"
        ]
        
        def animate_progress(step=0):
            if step < len(progress_messages) - 1:
                self.update_status(progress_messages[step])
                self.root.after(300, lambda: animate_progress(step + 1))
            else:
                # Final message will be set by the actual generation function
                pass
        
        animate_progress()
    
    def generate_timeline_embedded(self, data):
        """Generate timeline visualization and display as image in dashboard"""
        try:
            # Show progress
            self.show_status_progress()
            self.update_status_progress(0.1)
            self.update_status("Preparing timeline data...")
            
            # Clear existing content
            for widget in self.timeline_display.winfo_children():
                widget.destroy()
            
            self.update_status_progress(0.3)
            self.update_status("Processing annual storm data...")
            
            # Generate annual summary
            annual_data = self.data_processor.get_annual_storm_summary(data)
            
            if len(annual_data) == 0:
                self.hide_status_progress()
                error_label = ctk.CTkLabel(
                    self.timeline_display,
                    text="No annual data available for current filters",
                    font=ctk.CTkFont(size=14)
                )
                error_label.pack(pady=20)
                return
            
            self.update_status_progress(0.6)
            self.update_status("Creating timeline visualization...")
            
            # Create visualization
            fig = self.visualizer.create_timeline_overview(annual_data)
            
            self.update_status_progress(0.8)
            self.update_status("Rendering timeline image...")
            
            # Save as static image and display
            self.display_plotly_as_image(fig, self.timeline_display, "timeline")
            
            self.update_status_progress(0.95)
            self.update_status("Adding timeline summary...")
            
            # Add summary statistics
            self.add_timeline_summary(annual_data)
            
            # Complete
            self.update_status_progress(1.0)
            self.timeline_status.configure(text="Timeline generated successfully")
            self.update_status(f"Timeline complete • {len(annual_data)} years analyzed")
            
            # Hide progress after delay
            self.root.after(1000, self.hide_status_progress)
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error generating timeline: {str(e)}")
            error_label = ctk.CTkLabel(
                self.timeline_display,
                text=f"Error generating timeline: {str(e)}",
                font=ctk.CTkFont(size=14)
            )
            error_label.pack(pady=20)
    
    def generate_map_embedded(self, data):
        """Generate map visualization and display in dashboard"""
        try:
            # Show progress
            self.show_status_progress()
            self.update_status_progress(0.1)
            self.update_status("Preparing map data...")
            
            # Clear existing content
            for widget in self.map_display.winfo_children():
                widget.destroy()
            
            # Determine scope and limit based on dataset size
            scope = self.scope_var.get()
            map_scope = "atlantic" if scope == "Full Atlantic Basin" else "gulf"
            
            self.update_status_progress(0.3)
            self.update_status(f"Processing storm tracks for {scope}...")
            
            # Adjust storm limit based on scope (more storms for full Atlantic view)
            storm_limit = 20 if scope == "Full Atlantic Basin" else 10
            
            # Get storm tracks
            storm_tracks = self.data_processor.get_storm_tracks(data, limit=storm_limit)
            
            if not storm_tracks:
                self.hide_status_progress()
                error_label = ctk.CTkLabel(
                    self.map_display,
                    text="No storm track data available for current filters",
                    font=ctk.CTkFont(size=14)
                )
                error_label.pack(pady=20)
                return
            
            self.update_status_progress(0.6)
            self.update_status("Creating geographic visualization...")
            
            # Create visualization with appropriate scope
            title = f"Hurricane Tracks - {scope}"
            fig = self.visualizer.create_storm_track_map(storm_tracks, title=title, map_scope=map_scope)
            
            self.update_status_progress(0.8)
            self.update_status("Rendering map image...")
            
            # Save as static image and display
            self.display_plotly_as_image(fig, self.map_display, "map")
            
            self.update_status_progress(0.95)
            self.update_status("Adding map summary...")
            
            # Add map summary
            self.add_map_summary(storm_tracks, scope)
            
            # Complete
            self.update_status_progress(1.0)
            self.map_status.configure(text="Map generated successfully")
            self.update_status(f"Map complete • {len(storm_tracks)} storm tracks displayed")
            
            # Hide progress after delay
            self.root.after(1000, self.hide_status_progress)
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error generating map: {str(e)}")
            error_label = ctk.CTkLabel(
                self.map_display,
                text=f"Error generating map: {str(e)}",
                font=ctk.CTkFont(size=14)
            )
            error_label.pack(pady=20)
    
    def generate_analysis_embedded(self, data):
        """Generate analysis visualization and display in dashboard"""
        try:
            # Show progress
            self.show_status_progress()
            self.update_status_progress(0.1)
            self.update_status("Preparing analysis data...")
            
            # Clear existing content
            for widget in self.analysis_display.winfo_children():
                widget.destroy()
            
            self.update_status_progress(0.2)
            self.update_status("Calculating impact statistics...")
            
            # Generate impact statistics
            impact_stats = self.data_processor.get_impact_statistics(data)
            
            if not impact_stats:
                self.hide_status_progress()
                error_label = ctk.CTkLabel(
                    self.analysis_display,
                    text="No impact data available for current filters",
                    font=ctk.CTkFont(size=14)
                )
                error_label.pack(pady=20)
                return
            
            self.update_status_progress(0.4)
            self.update_status("Creating impact heatmap...")
            
            # Create multiple analysis visualizations
            # Impact heatmap
            heatmap_fig = self.visualizer.create_impact_heatmap(impact_stats)
            self.display_plotly_as_image(heatmap_fig, self.analysis_display, "heatmap")
            
            self.update_status_progress(0.7)
            self.update_status("Generating seasonal analysis...")
            
            # Seasonal analysis
            seasonal_fig = self.visualizer.create_seasonal_analysis(data)
            self.display_plotly_as_image(seasonal_fig, self.analysis_display, "seasonal")
            
            self.update_status_progress(0.9)
            self.update_status("Adding analysis summary...")
            
            # Add analysis summary
            self.add_analysis_summary(data, impact_stats)
            
            # Complete
            self.update_status_progress(1.0)
            self.analysis_status.configure(text="Analysis generated successfully")
            storm_count = data.groupby(['name', 'year']).size().count()
            self.update_status(f"Analysis complete • {storm_count} storms analyzed")
            
            # Hide progress after delay
            self.root.after(1000, self.hide_status_progress)
            
        except Exception as e:
            self.hide_status_progress()
            self.update_status(f"Error generating analysis: {str(e)}")
            error_label = ctk.CTkLabel(
                self.analysis_display,
                text=f"Error generating analysis: {str(e)}",
                font=ctk.CTkFont(size=14)
            )
            error_label.pack(pady=20)
    
    def display_plotly_as_image(self, fig, parent_frame, chart_type):
        """Convert Plotly figure to image and display in tkinter"""
        try:
            # Save figure as PNG in temp directory
            temp_dir = tempfile.mkdtemp()
            img_path = os.path.join(temp_dir, f"{chart_type}_{datetime.now().strftime('%H%M%S')}.png")
            
            # Export as static image
            fig.write_image(img_path, width=800, height=500)
            
            # Load and display image in tkinter
            from PIL import Image, ImageTk
            
            # Load image
            img = Image.open(img_path)
            # Resize if needed
            img = img.resize((750, 450), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Create label to display image
            img_label = tk.Label(parent_frame, image=photo, bg='#212121')
            img_label.image = photo  # Keep a reference
            img_label.pack(pady=10, padx=10)
            
            # Clean up temp file
            os.remove(img_path)
            os.rmdir(temp_dir)
            
        except ImportError:
            # Fallback if PIL or kaleido not available
            self.display_plotly_fallback(fig, parent_frame, chart_type)
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.display_plotly_fallback(fig, parent_frame, chart_type)
    
    def display_plotly_fallback(self, fig, parent_frame, chart_type):
        """Fallback method to display chart info when image generation fails"""
        # Create a summary of the chart instead of the actual image
        summary_frame = ctk.CTkFrame(parent_frame)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            summary_frame,
            text=f"📊 {chart_type.title()} Visualization Generated",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=10)
        
        info_label = ctk.CTkLabel(
            summary_frame,
            text=f"Interactive {chart_type} chart created successfully.\nUse 'Open in Browser' button for full interactivity.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        info_label.pack(pady=5)
    
    def add_timeline_summary(self, annual_data):
        """Add summary statistics below timeline"""
        summary_frame = ctk.CTkFrame(self.timeline_display)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            summary_frame,
            text="📈 Timeline Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        avg_storms = annual_data['storm_count'].mean()
        max_storms_year = annual_data.loc[annual_data['storm_count'].idxmax()]
        total_years = len(annual_data)
        
        stats_text = f"""Average Storms per Year: {avg_storms:.1f}
Most Active Year: {max_storms_year['year']} ({max_storms_year['storm_count']} storms)
Years Analyzed: {total_years}
Total Storm Count: {annual_data['storm_count'].sum()}"""
        
        stats_label = ctk.CTkLabel(
            summary_frame,
            text=stats_text.strip(),
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        stats_label.pack(pady=5)
    
    def add_map_summary(self, storm_tracks, scope="Gulf Coast Focus"):
        """Add summary statistics below map"""
        summary_frame = ctk.CTkFrame(self.map_display)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            summary_frame,
            text=f"🗺️ Map Summary - {scope}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        # Analyze storm tracks
        max_wind_storm = max(storm_tracks.values(), key=lambda x: x.get('max_wind', 0))
        storm_names = [track['name'] for track in storm_tracks.values()]
        
        # Calculate geographic span
        all_lats = []
        all_lons = []
        for track in storm_tracks.values():
            all_lats.extend([lat for lat in track['lats'] if lat is not None])
            all_lons.extend([lon for lon in track['lons'] if lon is not None])
        
        if all_lats and all_lons:
            lat_span = f"{min(all_lats):.1f}° to {max(all_lats):.1f}°N"
            lon_span = f"{min(all_lons):.1f}° to {max(all_lons):.1f}°W"
        else:
            lat_span = "N/A"
            lon_span = "N/A"
        
        stats_text = f"""Storms Displayed: {len(storm_tracks)}
Strongest Storm: {max_wind_storm['name']} ({max_wind_storm.get('max_wind', 0)} mph)
Geographic Coverage:
  Latitude: {lat_span}
  Longitude: {lon_span}
Sample Storms: {', '.join(storm_names[:3])}..."""
        
        stats_label = ctk.CTkLabel(
            summary_frame,
            text=stats_text.strip(),
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        stats_label.pack(pady=5)
    
    def add_analysis_summary(self, data, impact_stats):
        """Add summary statistics below analysis"""
        summary_frame = ctk.CTkFrame(self.analysis_display)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            summary_frame,
            text="📊 Analysis Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        # Calculate summary statistics
        total_records = len(data)
        unique_storms = data.groupby(['name', 'year']).size().count()
        avg_storms_per_year = impact_stats.get('avg_storms_per_year', 0)
        
        stats_text = f"""Total Records Analyzed: {total_records:,}
Unique Storms: {unique_storms}
Average Storms/Year: {avg_storms_per_year:.1f}
Peak Season: August - October"""
        
        stats_label = ctk.CTkLabel(
            summary_frame,
            text=stats_text.strip(),
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        stats_label.pack(pady=5)
    
    def create_timeline_placeholder(self):
        """Create timeline placeholder"""
        self.timeline_placeholder = ctk.CTkLabel(
            self.timeline_display,
            text="📊 Hurricane Timeline Visualization\n\nGenerate the timeline to see:\n• Annual storm frequency\n• Intensity trends over time\n• Statistical analysis\n• Interactive data exploration",
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        self.timeline_placeholder.pack(expand=True, pady=50)
    
    def create_map_placeholder(self):
        """Create map placeholder"""
        self.map_placeholder = ctk.CTkLabel(
            self.map_display,
            text="🗺️ Interactive Hurricane Track Map\n\nGenerate the map to see:\n• Storm paths and trajectories\n• Geographic impact areas\n• Intensity color coding\n• Gulf Coast boundaries",
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        self.map_placeholder.pack(expand=True, pady=50)
    
    def create_analysis_placeholder(self):
        """Create analysis placeholder"""
        self.analysis_placeholder = ctk.CTkLabel(
            self.analysis_display,
            text="📈 Hurricane Impact Analysis\n\nGenerate the analysis to see:\n• Impact frequency heatmaps\n• Seasonal pattern analysis\n• Intensity distributions\n• Statistical insights",
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        self.analysis_placeholder.pack(expand=True, pady=50)

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = HurricaneDashboard()
    app.run()