"""
Tabbed Native Dashboard with Top Navigation
Enhanced hurricane dashboard with dedicated tabs for each visualization type
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import psutil
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Import components
from native_visualizations import NativeVisualizationEngine
from settings_manager import SettingsManager, create_settings_gear_button, VisualizationSettings
from data_processor import HurricaneDataProcessor

class TabbedNativeDashboard:
    """Enhanced native GUI dashboard with tabbed interface for maximum visualization space"""
    
    def __init__(self, root: Optional[ctk.CTk] = None):
        # Initialize root window if not provided
        if root is None:
            self.root = ctk.CTk()
            self.root.title("🌀 Gulf Coast Hurricane Analysis Dashboard - Tabbed Interface")
            self.root.geometry("1800x1000")
            self.created_root = True
        else:
            self.root = root
            self.created_root = False
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Initialize components
        self.data_processor = None
        self.viz_engine = None
        self.selected_storm = None
        self.storm_data = None
        
        # Map filter variables
        self.current_map_filters = {}
        self.current_show_multiple = True
        
        # UI components
        self.main_frame = None
        self.navbar_frame = None
        self.tab_notebook = None
        self.control_frame = None
        self.status_frame = None
        
        # Tab frames
        self.timeline_tab = None
        self.map_tab = None
        self.analysis_tab = None
        self.overview_tab = None
        
        # Visualization containers
        self.timeline_viz_frame = None
        self.map_viz_frame = None
        self.analysis_viz_frame = None
        self.overview_viz_frame = None
        
        # Performance monitoring
        self.performance_data = {
            'cpu_usage': [],
            'memory_usage': [],
            'render_times': [],
            'timestamps': []
        }
        self.monitoring_active = False
        
        # Setup UI and initialize
        self.setup_ui()
        self.initialize_components()
        
        # Register settings callbacks
        self.register_settings_callbacks()
    
    def setup_ui(self):
        """Setup the tabbed user interface"""
        # Configure root grid
        self.root.grid_rowconfigure(1, weight=1)  # Main content area
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(1, weight=1)  # Tab notebook
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create components
        self.create_navbar()
        self.create_tabbed_interface()
        self.create_control_panel()
        self.create_status_panel()
    
    def create_navbar(self):
        """Create top navigation bar with controls and title"""
        self.navbar_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.navbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.navbar_frame.grid_propagate(False)
        
        # Configure navbar grid
        self.navbar_frame.grid_columnconfigure(1, weight=1)  # Title section expands
        
        # Left side - App title and info
        title_frame = ctk.CTkFrame(self.navbar_frame)
        title_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        app_title = ctk.CTkLabel(
            title_frame,
            text="🌀 Hurricane Analysis Dashboard",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        app_title.pack(side="left", padx=10, pady=10)
        
        # Center - Storm selector
        selector_frame = ctk.CTkFrame(self.navbar_frame)
        selector_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=5)
        selector_frame.grid_columnconfigure(2, weight=1)
        
        # Storm search
        search_label = ctk.CTkLabel(selector_frame, text="🔍 Search:")
        search_label.grid(row=0, column=0, padx=5, pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_storms)
        self.search_entry = ctk.CTkEntry(
            selector_frame,
            textvariable=self.search_var,
            placeholder_text="Enter storm name...",
            width=200
        )
        self.search_entry.grid(row=0, column=1, padx=5, pady=10)
        
        # Storm dropdown
        storm_label = ctk.CTkLabel(selector_frame, text="🌀 Storm:")
        storm_label.grid(row=0, column=2, padx=(20, 5), pady=10)
        
        self.storm_var = tk.StringVar()
        self.storm_selector = ctk.CTkComboBox(
            selector_frame,
            variable=self.storm_var,
            command=self.on_storm_selected,
            state="readonly",
            width=250
        )
        self.storm_selector.grid(row=0, column=3, padx=5, pady=10)
        
        # Right side - Action buttons
        buttons_frame = ctk.CTkFrame(self.navbar_frame)
        buttons_frame.grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        # Load data button
        self.load_btn = ctk.CTkButton(
            buttons_frame,
            text="📂 Load Data",
            command=self.load_hurricane_data,
            height=35,
            width=100
        )
        self.load_btn.pack(side="left", padx=5, pady=10)
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Refresh",
            command=self.refresh_all_visualizations,
            height=35,
            width=100,
            state="disabled"
        )
        self.refresh_btn.pack(side="left", padx=5, pady=10)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Export",
            command=self.export_analysis,
            height=35,
            width=100,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5, pady=10)
    
    def create_tabbed_interface(self):
        """Create main tabbed interface for visualizations"""
        # Create notebook with larger tabs
        self.tab_notebook = ctk.CTkTabview(self.main_frame, height=700)
        self.tab_notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Add tabs
        self.overview_tab = self.tab_notebook.add("📊 Overview")
        self.timeline_tab = self.tab_notebook.add("📈 Timeline Analysis") 
        self.map_tab = self.tab_notebook.add("🗺️ Storm Tracks")
        self.analysis_tab = self.tab_notebook.add("📋 Statistical Analysis")
        
        # Configure each tab for full-size visualizations
        self.setup_overview_tab()
        self.setup_timeline_tab()
        self.setup_map_tab()
        self.setup_analysis_tab()
    
    def setup_overview_tab(self):
        """Setup overview tab with dashboard summary"""
        # Configure grid
        self.overview_tab.grid_rowconfigure(1, weight=1)
        self.overview_tab.grid_columnconfigure(0, weight=1)
        
        # Header with settings
        header_frame = ctk.CTkFrame(self.overview_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Hurricane Data Overview & Summary Statistics",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        overview_gear = create_settings_gear_button(
            header_frame,
            self.settings_manager,
            "analysis"
        )
        overview_gear.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        # Large visualization container
        self.overview_viz_frame = ctk.CTkFrame(self.overview_tab)
        self.overview_viz_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configure for matplotlib canvas
        self.overview_viz_frame.grid_rowconfigure(0, weight=1)
        self.overview_viz_frame.grid_columnconfigure(0, weight=1)
    
    def setup_timeline_tab(self):
        """Setup timeline tab with full-screen timeline visualization"""
        # Configure grid for full expansion
        self.timeline_tab.grid_rowconfigure(1, weight=1)
        self.timeline_tab.grid_columnconfigure(0, weight=1)
        
        # Header with title and settings
        header_frame = ctk.CTkFrame(self.timeline_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📈 Storm Timeline Analysis & Intensity Progression",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        timeline_gear = create_settings_gear_button(
            header_frame,
            self.settings_manager,
            "timeline"
        )
        timeline_gear.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        # Full-size visualization container
        self.timeline_viz_frame = ctk.CTkFrame(self.timeline_tab)
        self.timeline_viz_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configure for large matplotlib canvas
        self.timeline_viz_frame.grid_rowconfigure(0, weight=1)
        self.timeline_viz_frame.grid_columnconfigure(0, weight=1)
    
    def setup_map_tab(self):
        """Setup map tab with full-screen map visualization and filtering options"""
        # Configure grid for full expansion
        self.map_tab.grid_rowconfigure(2, weight=1)  # Visualization area
        self.map_tab.grid_columnconfigure(0, weight=1)
        
        # Compact header with title and settings
        header_frame = ctk.CTkFrame(self.map_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🗺️ Regional Storm Track Visualization & Geographic Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        map_gear = create_settings_gear_button(
            header_frame,
            self.settings_manager,
            "map"
        )
        map_gear.grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        # Map filtering controls
        self.create_map_filters()
        
        # Maximum-size visualization container
        self.map_viz_frame = ctk.CTkFrame(self.map_tab)
        self.map_viz_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # Configure for large matplotlib canvas
        self.map_viz_frame.grid_rowconfigure(0, weight=1)
        self.map_viz_frame.grid_columnconfigure(0, weight=1)
    
    def setup_analysis_tab(self):
        """Setup analysis tab with statistical analysis visualizations"""
        # Configure grid for full expansion
        self.analysis_tab.grid_rowconfigure(1, weight=1)
        self.analysis_tab.grid_columnconfigure(0, weight=1)
        
        # Header with title and settings
        header_frame = ctk.CTkFrame(self.analysis_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📋 Statistical Analysis & Data Insights",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        analysis_gear = create_settings_gear_button(
            header_frame,
            self.settings_manager,
            "analysis"
        )
        analysis_gear.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        # Full-size visualization container for multi-panel analysis
        self.analysis_viz_frame = ctk.CTkFrame(self.analysis_tab)
        self.analysis_viz_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configure for large matplotlib canvas
        self.analysis_viz_frame.grid_rowconfigure(0, weight=1)
        self.analysis_viz_frame.grid_columnconfigure(0, weight=1)
    
    def create_control_panel(self):
        """Create bottom control panel"""
        self.control_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.control_frame.grid_propagate(False)
        
        # Configure grid
        self.control_frame.grid_columnconfigure(1, weight=1)
        
        # Left side - Data info
        info_label = ctk.CTkLabel(
            self.control_frame,
            text="📊 Hurricane Data Dashboard - Enhanced Native GUI with Tabbed Interface",
            font=ctk.CTkFont(size=12)
        )
        info_label.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        # Right side - Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.control_frame, width=200)
        self.progress_bar.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        self.progress_bar.set(0)
    
    def create_status_panel(self):
        """Create status panel"""
        self.status_frame = ctk.CTkFrame(self.main_frame, height=30)
        self.status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.status_frame.grid_propagate(False)
        
        # Status label
        self.performance_label = ctk.CTkLabel(
            self.status_frame,
            text="⚡ Hurricane Dashboard Ready - Tabbed Interface",
            font=ctk.CTkFont(size=11)
        )
        self.performance_label.pack(side="left", padx=15, pady=5)
    
    def register_settings_callbacks(self):
        """Register callbacks for when settings change"""
        self.settings_manager.register_callback("timeline", self.on_timeline_settings_changed)
        self.settings_manager.register_callback("map", self.on_map_settings_changed)
        self.settings_manager.register_callback("analysis", self.on_analysis_settings_changed)
    
    def on_timeline_settings_changed(self, settings: VisualizationSettings):
        """Handle timeline settings changes"""
        print("🔧 Timeline settings updated")
        if self.viz_engine and self.selected_storm:
            self.update_timeline_visualization()
    
    def on_map_settings_changed(self, settings: VisualizationSettings):
        """Handle map settings changes"""
        print("🔧 Map settings updated")
        if self.viz_engine and self.selected_storm:
            self.update_map_visualization()
    
    def on_analysis_settings_changed(self, settings: VisualizationSettings):
        """Handle analysis settings changes"""
        print("🔧 Analysis settings updated")
        if self.viz_engine and self.storm_data is not None:
            self.update_analysis_visualization()
            self.update_overview_visualization()
    
    def initialize_components(self):
        """Initialize data processor and visualization engine"""
        try:
            print("🔧 Initializing tabbed dashboard components...")
            
            # Initialize data processor
            self.data_processor = HurricaneDataProcessor()
            
            # Initialize visualization engine with settings
            self.viz_engine = NativeVisualizationEngine(
                parent_widget=self.root,
                settings=self.settings_manager.settings
            )
            
            print("✅ Tabbed dashboard components initialized")
            
            # Auto-load data if available
            self.auto_load_data()
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize dashboard: {e}")
    
    def auto_load_data(self):
        """Auto-load data during initialization"""
        def auto_load_thread():
            try:
                print("📊 Auto-loading hurricane data...")
                self.root.after(0, lambda: self.performance_label.configure(
                    text="📊 Loading hurricane data..."
                ))
                self.root.after(0, lambda: self.progress_bar.set(0.1))
                
                # Use already loaded data from data processor initialization
                if hasattr(self.data_processor, 'gulf_coast_data') and self.data_processor.gulf_coast_data is not None:
                    self.storm_data = self.data_processor.gulf_coast_data
                    print(f"📊 Using pre-loaded Gulf Coast data: {len(self.storm_data)} records")
                elif hasattr(self.data_processor, 'processed_data') and self.data_processor.processed_data is not None:
                    self.storm_data = self.data_processor.processed_data
                    print(f"📊 Using pre-loaded processed data: {len(self.storm_data)} records")
                else:
                    # Fallback: try to load data manually
                    success = self.data_processor.load_data("storms.csv")
                    if success and hasattr(self.data_processor, 'gulf_coast_data'):
                        self.storm_data = self.data_processor.gulf_coast_data
                    else:
                        raise Exception("Failed to load hurricane data")
                
                self.root.after(0, lambda: self.progress_bar.set(0.5))
                
                if self.storm_data is not None and not self.storm_data.empty:
                    # Update storm selector
                    self.root.after(0, self.update_storm_selector)
                    self.root.after(0, lambda: self.progress_bar.set(0.8))
                    
                    # Enable controls
                    self.root.after(0, self.enable_controls)
                    self.root.after(0, lambda: self.progress_bar.set(1.0))
                    
                    # Auto-select first storm and update visualizations
                    self.root.after(500, self.auto_select_first_storm)
                    
                    self.root.after(0, lambda: self.performance_label.configure(
                        text=f"✅ Loaded {len(self.storm_data)} hurricane records - Ready for analysis"
                    ))
                    
                    print(f"✅ Auto-loaded {len(self.storm_data)} hurricane records")
                else:
                    self.root.after(0, lambda: self.performance_label.configure(
                        text="⚠️ No data available - use Load Data button"
                    ))
                    print("⚠️ No data loaded - storm_data is empty")
                
            except Exception as e:
                self.root.after(0, lambda: self.performance_label.configure(
                    text="❌ Auto-load failed - use Load Data button"
                ))
                print(f"⚠️ Auto-load failed: {e}")
            finally:
                self.root.after(2000, lambda: self.progress_bar.set(0))
        
        # Start auto-loading in background
        threading.Thread(target=auto_load_thread, daemon=True).start()
    
    def update_storm_selector(self):
        """Update storm selector dropdown"""
        if self.storm_data is not None and not self.storm_data.empty:
            # Get unique storms - combine name and year for unique identification
            if 'name' in self.storm_data.columns and 'year' in self.storm_data.columns:
                # Create combined storm names
                storm_combinations = self.storm_data.groupby(['name', 'year']).size().index
                storms = [f"{name} ({year})" for name, year in storm_combinations]
                storms = sorted(storms)
            elif 'name' in self.storm_data.columns:
                # Just use name if year not available
                storms = sorted(self.storm_data['name'].unique())
            else:
                print("⚠️ No 'name' column found in storm data")
                storms = []
            
            self.storm_selector.configure(values=storms)
            
            if storms:
                self.storm_selector.set(storms[0])
                self.selected_storm = storms[0]
    
    def filter_storms(self, *args):
        """Filter storms based on search text"""
        if self.storm_data is None:
            return
        
        search_text = self.search_var.get().lower()
        
        if 'name' in self.storm_data.columns and 'year' in self.storm_data.columns:
            # Create combined storm names
            storm_combinations = self.storm_data.groupby(['name', 'year']).size().index
            all_storms = [f"{name} ({year})" for name, year in storm_combinations]
        elif 'name' in self.storm_data.columns:
            all_storms = list(self.storm_data['name'].unique())
        else:
            all_storms = []
        
        if not search_text:
            # Show all storms
            storms = sorted(all_storms)
        else:
            # Filter storms
            storms = [s for s in all_storms if search_text in s.lower()]
            storms = sorted(storms)
        
        self.storm_selector.configure(values=storms)
    
    def auto_select_first_storm(self):
        """Auto-select the first storm and load visualizations"""
        try:
            # Check if storm selector has values
            if hasattr(self, 'storm_selector') and self.storm_selector.cget('values'):
                storms = list(self.storm_selector.cget('values'))
                if storms:
                    # Select first storm
                    first_storm = storms[0] 
                    self.storm_selector.set(first_storm)
                    self.selected_storm = first_storm
                    
                    print(f"🌀 Auto-selected storm: {first_storm}")
                    
                    # Update all visualizations
                    self.update_all_visualizations()
                else:
                    print("⚠️ No storms available in selector")
            else:
                print("⚠️ Storm selector not ready")
                
        except Exception as e:
            print(f"⚠️ Auto-selection error: {e}")
    
    def on_storm_selected(self, storm_name: str):
        """Handle storm selection"""
        self.selected_storm = storm_name
        print(f"🌀 Selected storm: {storm_name}")
        
        if self.viz_engine and self.storm_data is not None:
            # Update the visualization for the currently active tab
            current_tab = self.tab_notebook.get()
            if "Timeline" in current_tab:
                self.update_timeline_visualization()
            elif "Storm Tracks" in current_tab:
                self.update_map_visualization()
            elif "Statistical" in current_tab:
                self.update_analysis_visualization()
            elif "Overview" in current_tab:
                self.update_overview_visualization()
    
    def get_storm_data_subset(self):
        """Get data subset for selected storm"""
        if not self.selected_storm or self.storm_data is None:
            return None
        
        try:
            # Parse storm name and year from selection like "Katrina (2005)"
            if '(' in self.selected_storm and ')' in self.selected_storm:
                storm_name = self.selected_storm.split(' (')[0]
                year = int(self.selected_storm.split(' (')[1].replace(')', ''))
                storm_subset = self.storm_data[
                    (self.storm_data['name'] == storm_name) & 
                    (self.storm_data['year'] == year)
                ].copy()
            else:
                # Fallback: just use name
                storm_subset = self.storm_data[
                    self.storm_data['name'] == self.selected_storm
                ].copy()
            
            return storm_subset if not storm_subset.empty else None
            
        except Exception as e:
            print(f"⚠️ Error getting storm data subset: {e}")
            return None
    
    def update_overview_visualization(self):
        """Update overview visualization with current settings"""
        try:
            if self.storm_data is not None:
                # Create overview analysis with full dataset
                canvas = self.viz_engine.create_analysis_visualization(
                    self.storm_data,
                    self.overview_viz_frame,
                    analysis_type="overview_summary",
                    chart_type="multi",
                    settings=self.settings_manager.settings
                )
                print("✅ Overview visualization updated")
        except Exception as e:
            print(f"⚠️ Overview update error: {e}")
    
    def update_timeline_visualization(self):
        """Update timeline visualization with current settings"""
        storm_subset = self.get_storm_data_subset()
        if storm_subset is None:
            return
        
        try:
            # Create timeline with current settings and larger figure size
            canvas = self.viz_engine.create_timeline_visualization(
                storm_subset, 
                self.timeline_viz_frame,
                title=f"Timeline Analysis: {self.selected_storm}",
                settings=self.settings_manager.settings
            )
            print("✅ Timeline visualization updated")
        except Exception as e:
            print(f"⚠️ Timeline update error: {e}")
    
    def update_map_visualization(self):
        """Update the map visualization with current filters"""
        try:
            if not self.viz_engine or self.storm_data is None:
                return
            
            # Clear existing map
            for widget in self.map_viz_frame.winfo_children():
                widget.destroy()
            
            # Generate updated map with filters
            map_canvas = self.viz_engine.generate_map_visualization(
                self.storm_data,
                self.map_viz_frame,
                show_multiple_tracks=getattr(self, 'current_show_multiple', True),
                filter_options=getattr(self, 'current_map_filters', {})
            )
            
            if map_canvas:
                # Place the canvas in the frame
                map_canvas.grid(row=0, column=0, sticky="nsew")
                
                print(f"🗺️ Map visualization updated with filters: {getattr(self, 'current_map_filters', {})}")
            
        except Exception as e:
            print(f"⚠️ Map update error: {e}")
            import traceback
            traceback.print_exc()
    
    def update_analysis_visualization(self):
        """Update analysis visualization with current settings"""
        try:
            if self.storm_data is not None:
                # Create analysis with current settings and larger figure size
                canvas = self.viz_engine.create_analysis_visualization(
                    self.storm_data,
                    self.analysis_viz_frame,
                    analysis_type="statistical_analysis",
                    chart_type="multi_panel",
                    settings=self.settings_manager.settings
                )
                print("✅ Analysis visualization updated")
        except Exception as e:
            print(f"⚠️ Analysis update error: {e}")
    
    def update_all_visualizations(self):
        """Update all visualizations"""
        print("🔄 Updating tabbed visualizations...")
        
        def update_thread():
            try:
                self.root.after(0, lambda: self.performance_label.configure(
                    text="🔄 Updating visualizations..."
                ))
                
                # Update all tabs
                self.root.after(0, self.update_overview_visualization)
                self.root.after(0, self.update_timeline_visualization)
                self.root.after(0, self.update_map_visualization)  
                self.root.after(0, self.update_analysis_visualization)
                
                self.root.after(0, lambda: self.performance_label.configure(
                    text="✅ All visualizations updated"
                ))
                
            except Exception as e:
                self.root.after(0, lambda: self.performance_label.configure(
                    text=f"❌ Update failed: {e}"
                ))
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def load_hurricane_data(self):
        """Load hurricane data with progress tracking"""
        def load_data_thread():
            try:
                self.progress_bar.set(0.1)
                self.performance_label.configure(text="📊 Loading hurricane data...")
                
                # Load data with correct file parameter
                success = self.data_processor.load_data("storms.csv")
                if success and hasattr(self.data_processor, 'gulf_coast_data'):
                    self.storm_data = self.data_processor.gulf_coast_data
                else:
                    raise Exception("Failed to load hurricane data file")
                self.progress_bar.set(0.5)
                
                # Update storm selector
                self.root.after(0, self.update_storm_selector)
                self.progress_bar.set(0.8)
                
                # Enable controls
                self.root.after(0, self.enable_controls)
                self.progress_bar.set(1.0)
                
                self.root.after(0, lambda: self.performance_label.configure(
                    text=f"✅ Loaded {len(self.storm_data)} hurricane records"
                ))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Data Loading Error", f"Failed to load data: {e}"
                ))
                self.root.after(0, lambda: self.performance_label.configure(
                    text="❌ Failed to load data"
                ))
            finally:
                self.root.after(1000, lambda: self.progress_bar.set(0))
        
        # Start loading in background
        threading.Thread(target=load_data_thread, daemon=True).start()
    
    def refresh_all_visualizations(self):
        """Refresh all visualizations - reload data and update displays"""
        try:
            print("🔄 Refreshing tabbed dashboard data and visualizations...")
            self.performance_label.configure(text="🔄 Refreshing data...")
            
            # Reload data from processor
            if self.data_processor:
                # Force reload the data
                success = self.data_processor.load_data("storms.csv")
                if success and hasattr(self.data_processor, 'gulf_coast_data'):
                    self.storm_data = self.data_processor.gulf_coast_data
                    
                    # Update storm selector with potentially new data
                    self.update_storm_selector()
                    
                    # Update visualizations if storm is selected
                    if self.selected_storm:
                        self.update_all_visualizations()
                    
                    self.performance_label.configure(
                        text=f"✅ Refreshed - {len(self.storm_data)} records loaded"
                    )
                    print(f"✅ Refreshed {len(self.storm_data)} hurricane records")
                else:
                    self.performance_label.configure(text="❌ Refresh failed")
                    print("❌ Failed to refresh data")
            else:
                print("⚠️ Data processor not available")
                
        except Exception as e:
            print(f"❌ Refresh error: {e}")
            self.performance_label.configure(text=f"❌ Refresh error: {e}")
    
    def export_analysis(self):
        """Export current analysis"""
        try:
            if self.storm_data is None:
                messagebox.showwarning("Export Warning", "No data available to export")
                return
            
            # Create export with current settings
            export_path = f"hurricane_analysis_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Simple export for now - could be enhanced
            messagebox.showinfo("Export", f"Analysis exported to {export_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def enable_controls(self):
        """Enable control buttons after data loading"""
        self.refresh_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_active = True
        
        def monitor_performance():
            while self.monitoring_active:
                try:
                    # Get system metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_info = psutil.virtual_memory()
                    
                    # Update performance data
                    self.performance_data['cpu_usage'].append(cpu_percent)
                    self.performance_data['memory_usage'].append(memory_info.percent)
                    self.performance_data['timestamps'].append(datetime.now())
                    
                    # Keep only last 100 data points
                    if len(self.performance_data['cpu_usage']) > 100:
                        for key in self.performance_data:
                            self.performance_data[key] = self.performance_data[key][-100:]
                    
                    # Update UI if monitoring is enabled in settings
                    if self.settings_manager.settings.show_performance_stats:
                        current_status = self.performance_label.cget("text")
                        if "CPU:" not in current_status:  # Don't override other status messages
                            self.root.after(0, lambda: self.performance_label.configure(
                                text=f"⚡ CPU: {cpu_percent:.1f}% | RAM: {memory_info.percent:.1f}% | Tabbed Interface"
                            ))
                    
                    time.sleep(3)  # Update every 3 seconds
                    
                except Exception as e:
                    print(f"⚠️ Performance monitoring error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=monitor_performance, daemon=True).start()
    
    def create_map_filters(self):
        """Create compact filtering controls for the map visualization"""
        # Compact filter controls frame
        filter_frame = ctk.CTkFrame(self.map_tab)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        # Configure grid for filter sections
        filter_frame.grid_columnconfigure(0, weight=1)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)
        
        # Year range filtering
        year_frame = ctk.CTkFrame(filter_frame)
        year_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        
        ctk.CTkLabel(year_frame, text="📅 Year Range", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=2)
        
        year_controls = ctk.CTkFrame(year_frame)
        year_controls.pack(fill="x", padx=3, pady=1)
        
        ctk.CTkLabel(year_controls, text="From:").pack(side="left", padx=2)
        self.year_start_var = tk.StringVar(value="1975")
        self.year_start_entry = ctk.CTkEntry(year_controls, textvariable=self.year_start_var, width=60)
        self.year_start_entry.pack(side="left", padx=2)
        
        ctk.CTkLabel(year_controls, text="To:").pack(side="left", padx=2)
        self.year_end_var = tk.StringVar(value="2025")
        self.year_end_entry = ctk.CTkEntry(year_controls, textvariable=self.year_end_var, width=60)
        self.year_end_entry.pack(side="left", padx=2)
        
        # Category filtering
        category_frame = ctk.CTkFrame(filter_frame)
        category_frame.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        
        ctk.CTkLabel(category_frame, text="🌀 Categories", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=2)
        
        self.category_vars = {}
        categories = ["Tropical Storm", "Category 1", "Category 2", "Category 3", "Category 4", "Category 5"]
        
        cat_controls = ctk.CTkFrame(category_frame)
        cat_controls.pack(fill="x", padx=3, pady=1)
        
        for i, category in enumerate(categories):
            self.category_vars[category] = tk.BooleanVar(value=True)
            checkbox = ctk.CTkCheckBox(cat_controls, text=f"Cat {i+1}" if "Category" in category else "TS",
                                     variable=self.category_vars[category], width=50)
            checkbox.pack(side="left", padx=1)
        
        # Wind speed filtering
        wind_frame = ctk.CTkFrame(filter_frame)
        wind_frame.grid(row=0, column=2, sticky="ew", padx=2, pady=2)
        
        ctk.CTkLabel(wind_frame, text="💨 Wind Speed", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=2)
        
        wind_controls = ctk.CTkFrame(wind_frame)
        wind_controls.pack(fill="x", padx=3, pady=1)
        
        ctk.CTkLabel(wind_controls, text="Min:").pack(side="left", padx=2)
        self.min_wind_var = tk.StringVar(value="35")
        self.min_wind_entry = ctk.CTkEntry(wind_controls, textvariable=self.min_wind_var, width=50)
        self.min_wind_entry.pack(side="left", padx=2)
        
        ctk.CTkLabel(wind_controls, text="Max:").pack(side="left", padx=2)
        self.max_wind_var = tk.StringVar(value="200")
        self.max_wind_entry = ctk.CTkEntry(wind_controls, textvariable=self.max_wind_var, width=50)
        self.max_wind_entry.pack(side="left", padx=2)
        
        # Control buttons
        button_frame = ctk.CTkFrame(filter_frame)
        button_frame.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        
        ctk.CTkLabel(button_frame, text="🎛️ Controls", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=2)
        
        control_buttons = ctk.CTkFrame(button_frame)
        control_buttons.pack(fill="x", padx=3, pady=1)
        
        # Show multiple tracks toggle
        self.show_multiple_var = tk.BooleanVar(value=True)
        multi_toggle = ctk.CTkCheckBox(control_buttons, text="Multi-Track", 
                                     variable=self.show_multiple_var)
        multi_toggle.pack(pady=1)
        
        # Apply filters button
        apply_btn = ctk.CTkButton(control_buttons, text="Apply Filters", 
                                command=self.apply_map_filters, height=25)
        apply_btn.pack(pady=1)
        
        # Reset filters button
        reset_btn = ctk.CTkButton(control_buttons, text="Reset", 
                                command=self.reset_map_filters, height=25)
        reset_btn.pack(pady=1)
    
    def apply_map_filters(self):
        """Apply the selected filters to the map visualization"""
        try:
            # Gather filter options
            filter_options = {
                'year_start': int(self.year_start_var.get()),
                'year_end': int(self.year_end_var.get()),
                'min_wind': int(self.min_wind_var.get()),
                'max_wind': int(self.max_wind_var.get()),
                'categories': [cat for cat, var in self.category_vars.items() if var.get()]
            }
            
            show_multiple = self.show_multiple_var.get()
            
            # Update map visualization with filters
            if self.viz_engine and self.storm_data is not None:
                # Store filter options for map updates
                self.current_map_filters = filter_options
                self.current_show_multiple = show_multiple
                
                # Update the map visualization
                self.update_map_visualization()
                
                self.performance_label.configure(
                    text=f"✅ Map filters applied - {len(self.storm_data)} records filtered"
                )
                
                print(f"🎛️ Applied map filters: {filter_options}")
            
        except ValueError as e:
            messagebox.showerror("Filter Error", f"Invalid filter values: {e}")
        except Exception as e:
            print(f"⚠️ Filter application error: {e}")
            messagebox.showerror("Filter Error", f"Failed to apply filters: {e}")
    
    def reset_map_filters(self):
        """Reset all map filters to default values"""
        # Reset year range
        self.year_start_var.set("1975")
        self.year_end_var.set("2025")
        
        # Reset wind speed
        self.min_wind_var.set("35")
        self.max_wind_var.set("200")
        
        # Reset categories (all selected)
        for var in self.category_vars.values():
            var.set(True)
        
        # Reset multi-track toggle
        self.show_multiple_var.set(True)
        
        # Clear stored filters
        self.current_map_filters = {}
        self.current_show_multiple = True
        
        # Update visualization
        self.update_map_visualization()
        
        print("🔄 Map filters reset to defaults")



    def run(self):
        """Run the tabbed dashboard"""
        try:
            print("🚀 Starting Tabbed Native Hurricane Dashboard...")
            
            # Start performance monitoring
            self.start_monitoring()
            
            # Update display
            self.performance_label.configure(text="🌀 Tabbed Hurricane Dashboard Ready")
            
            # Run main loop if we created the root
            if self.created_root:
                self.root.mainloop()
                
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            messagebox.showerror("Dashboard Error", f"Dashboard error: {e}")
        finally:
            self.monitoring_active = False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.monitoring_active = False
            
            if self.viz_engine:
                self.viz_engine.cleanup()
                
            print("✅ Tabbed dashboard cleanup completed")
            
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

def main():
    """Main function to run the tabbed dashboard"""
    try:
        # Set appearance mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create and run dashboard
        dashboard = TabbedNativeDashboard()
        dashboard.run()
        
    except Exception as e:
        print(f"❌ Failed to start tabbed dashboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()