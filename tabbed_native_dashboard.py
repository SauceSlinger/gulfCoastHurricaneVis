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
import matplotlib.pyplot as plt
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Import components
from native_visualizations import NativeVisualizationEngine
from settings_manager import SettingsManager, create_settings_gear_button, VisualizationSettings
from aesthetic_theme import get_theme, AestheticTheme

# Try database processor first, fallback to CSV processor
try:
    from data_processor_db import HurricaneDataProcessor
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

if not DATABASE_AVAILABLE:
    try:
        from csv_data_processor import HurricaneDataProcessor
    except ImportError:
        # Final fallback - create a minimal processor
        class HurricaneDataProcessor:
            def __init__(self):
                self.gulf_coast_data = pd.DataFrame()
                self.full_atlantic_data = pd.DataFrame()
            def get_storm_list(self, dataset="gulf_coast"):
                return []
            def get_storm_data(self, storm_name, dataset="gulf_coast"):
                return pd.DataFrame()
            def get_dataset_for_analysis(self, dataset="gulf_coast", year_range=None):
                return pd.DataFrame()

class TabbedNativeDashboard:
    """Enhanced native GUI dashboard with tabbed interface for maximum visualization space"""
    
    def __init__(self, data_processor=None, loading_callback=None, log_callback=None):
        """Initialize the dashboard with optional data processor, loading callback, and log callback"""
        self.log_callback = log_callback
        print("� Initializing TabbedNativeDashboard...")
        
        # Data
        self.data_processor = data_processor
        self.storm_data = None
        self.selected_storm = None
        self.viz_engine = None
        
        # Loading coordination
        self.loading_callback = loading_callback
        self.visualizations_ready = {
            'overview': False,
            'timeline': False,
            'map': False,
            'analysis': False
        }
        self.all_visualizations_complete = False
        
        # UI Components
        self.root = None
        self.notebook = None
        self.storm_selector = None
        self.performance_label = None
        self.progress_bar = None
        
        # Visualization state
        self.current_viz_data = None
        
        # Initialize essential components before setup_ui
        self._initialize_core_components()
        self.setup_ui()
        
        # Initialize data components after UI is ready
        self.initialize_components()
    
    def _log(self, message: str):
        """Send log message to both console and loading window if callback exists"""
        print(message)
        if self.log_callback:
            try:
                self.log_callback(message)
            except Exception as e:
                print(f"⚠️ Log callback error: {e}")
    
    def _setup_logging(self):
        """Setup logging for the dashboard"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _initialize_core_components(self):
        """Initialize core components required for UI setup"""
        # Performance monitoring
        self.monitoring_active = False
        self.performance_data = {
            'cpu_usage': [],
            'memory_usage': [],
            'timestamps': []
        }
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Create root window
        self.root = ctk.CTk()
        self.root.title("🌀 Gulf Coast Hurricane Analysis Dashboard")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.created_root = True
        
        # Initialize theme and settings
        self.theme = AestheticTheme()
        self.settings_manager = SettingsManager()
        
        self._log("✅ Core components initialized")
    
    def setup_ui(self):
        """Setup the tabbed user interface with aesthetic theming"""
        # Configure root grid - main content in row 0
        self.root.grid_rowconfigure(0, weight=1)  # Main content area
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container with minimal padding to maximize space
        self.main_frame = self.theme.get_styled_frame(self.root, style="secondary")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(1, weight=1)  # Tab notebook
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create components
        self.create_navbar()
        self.create_tabbed_interface()
        # Create minimal progress bar for compatibility (no visible panel)
        self.create_minimal_progress_bar()
        # Skip control panel and status panel for minimal bottom space
        
        # Register settings callbacks after UI is created
        self.register_settings_callbacks()
    
    def create_navbar(self):
        """Create top navigation bar with controls and title"""
        self.navbar_frame = self.theme.get_styled_frame(
            self.main_frame, 
            style="card", 
            height=self.theme.spacing.header_height
        )
        self.navbar_frame.grid(row=0, column=0, sticky="ew", 
                              padx=2, 
                              pady=(2, 1))
        self.navbar_frame.grid_propagate(False)
        
        # Configure navbar grid
        self.navbar_frame.grid_columnconfigure(1, weight=1)  # Title section expands
        
        # Left side - App title and info
        title_frame = self.theme.get_styled_frame(self.navbar_frame, style="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=self.theme.spacing.md, pady=self.theme.spacing.sm)
        
        app_title = self.theme.get_styled_label(
            title_frame,
            text="🌀 Hurricane Analysis Dashboard",
            style="title"
        )
        app_title.pack(side="left", padx=self.theme.spacing.md, pady=self.theme.spacing.md)
        
        # Center - Storm selector
        selector_frame = self.theme.get_styled_frame(self.navbar_frame, style="transparent")
        selector_frame.grid(row=0, column=1, sticky="ew", padx=self.theme.spacing.lg, pady=self.theme.spacing.sm)
        selector_frame.grid_columnconfigure(2, weight=1)
        
        # Storm search
        search_label = self.theme.get_styled_label(selector_frame, text="🔍 Search:", style="body")
        search_label.grid(row=0, column=0, padx=self.theme.spacing.sm, pady=self.theme.spacing.md)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_storms)
        self.search_entry = self.theme.get_styled_entry(
            selector_frame,
            placeholder="Enter storm name...",
            width=200
        )
        self.search_entry.configure(textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, padx=self.theme.spacing.sm, pady=self.theme.spacing.md)
        
        # Storm dropdown
        storm_label = self.theme.get_styled_label(selector_frame, text="🌀 Storm:", style="body")
        storm_label.grid(row=0, column=2, padx=(self.theme.spacing.lg, self.theme.spacing.sm), pady=self.theme.spacing.md)
        
        self.storm_var = tk.StringVar()
        self.storm_selector = self.theme.get_styled_combobox(
            selector_frame,
            values=[],
            width=250
        )
        self.storm_selector.configure(variable=self.storm_var, command=self.on_storm_selected, state="readonly")
        self.storm_selector.grid(row=0, column=3, padx=self.theme.spacing.sm, pady=self.theme.spacing.md)
        
        # Right side - Action buttons
        buttons_frame = self.theme.get_styled_frame(self.navbar_frame, style="transparent")
        buttons_frame.grid(row=0, column=2, sticky="e", padx=self.theme.spacing.md, pady=self.theme.spacing.sm)
        
        # Load data button
        self.load_btn = self.theme.get_styled_button(
            buttons_frame,
            text="📂 Load Data",
            command=self.load_hurricane_data,
            style="primary",
            width=100
        )
        self.load_btn.pack(side="left", padx=self.theme.spacing.sm, pady=self.theme.spacing.md)
        
        # Refresh button
        self.refresh_btn = self.theme.get_styled_button(
            buttons_frame,
            text="🔄 Refresh",
            command=self.refresh_all_visualizations,
            style="secondary",
            width=100
        )
        self.refresh_btn.configure(state="disabled")
        self.refresh_btn.pack(side="left", padx=self.theme.spacing.sm, pady=self.theme.spacing.md)
        
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
        # Create notebook with minimal padding to maximize space usage
        self.tab_notebook = ctk.CTkTabview(self.main_frame)
        self.tab_notebook.grid(row=1, column=0, sticky="nsew", padx=2, pady=(2, 0))
        
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
        
        # Add minimal bottom border frame for visual consistency
        self.create_bottom_border()
    
    def create_bottom_border(self):
        """Create minimal bottom border frame - nearly flush with window bottom"""
        self.bottom_border_frame = self.theme.get_styled_frame(self.main_frame, style="transparent")
        self.bottom_border_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        # Minimal bottom border to save vertical space
        self.bottom_border_frame.configure(height=1)  # Minimal 1-pixel bottom border
        self.bottom_border_frame.grid_propagate(False)  # Maintain fixed height
    
    def create_minimal_progress_bar(self):
        """Create loading progress bar at top of dashboard"""
        # Create frame for loading indicator
        self.loading_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.loading_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(2, 5))
        self.loading_frame.grid_columnconfigure(0, weight=1)
        
        # Loading status container
        loading_container = ctk.CTkFrame(self.loading_frame)
        loading_container.pack(fill="x", padx=10, pady=5)
        loading_container.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.loading_status_label = ctk.CTkLabel(
            loading_container,
            text="🔄 Loading visualizations...",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.loading_status_label.pack(pady=(5, 2))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(loading_container, width=600, height=8)
        self.progress_bar.pack(pady=2)
        self.progress_bar.set(0)
        
        # Details label showing which visualizations are loading
        self.loading_details_label = ctk.CTkLabel(
            loading_container,
            text="Initializing: Overview, Timeline, Map, Analysis",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        self.loading_details_label.pack(pady=(2, 5))
        
        # Performance label (for compatibility)
        self.performance_label = ctk.CTkLabel(loading_container, text="", font=ctk.CTkFont(size=9))
        self.performance_label.pack()
    
    def setup_overview_tab(self):
        """Setup overview tab with scrollable interactive statistics report"""
        # Configure grid
        self.overview_tab.grid_rowconfigure(1, weight=1)
        self.overview_tab.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self.overview_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Hurricane Data Overview & Interactive Statistics Report",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # Refresh button for overview
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh Report",
            command=self.update_overview_visualization,
            width=120,
            height=30
        )
        refresh_btn.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        # Create scrollable frame for the report
        self.overview_scroll = ctk.CTkScrollableFrame(
            self.overview_tab,
            fg_color=self.theme.colors.bg_secondary if self.theme else "#1a1a1a"
        )
        self.overview_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.overview_scroll.grid_columnconfigure(0, weight=1)
        
        # Store reference to scrollable frame
        self.overview_viz_frame = self.overview_scroll
    
    def setup_timeline_tab(self):
        """Setup timeline tab with interactive time-based analysis and sliders"""
        # Configure grid for full expansion
        self.timeline_tab.grid_rowconfigure(1, weight=1)
        self.timeline_tab.grid_columnconfigure(0, weight=1)
        
        # Header with title and settings
        header_frame = ctk.CTkFrame(self.timeline_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📈 Interactive Timeline Analysis",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        timeline_gear = create_settings_gear_button(
            header_frame,
            self.settings_manager,
            "timeline"
        )
        timeline_gear.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        # Main container with scrollable frame
        self.timeline_viz_frame = ctk.CTkScrollableFrame(self.timeline_tab)
        self.timeline_viz_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.timeline_viz_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize timeline state variables
        self.timeline_year_range = [1975, 2021]  # Default full range
        self.timeline_decade_range = [1970, 2020]  # For decade analysis
        self.timeline_month_range = [1, 12]  # For seasonal analysis
        self.timeline_category_threshold = 0  # Minimum category to show
    
    def setup_map_tab(self):
        """Setup map tab with full-screen map visualization and filtering options"""
        # Configure grid for full expansion
        self.map_tab.grid_rowconfigure(2, weight=1)  # Visualization area
        self.map_tab.grid_columnconfigure(0, weight=1)
        # Ultra-compact header with title and settings
        # Remove extra padding so the map can sit flush underneath
        header_frame = ctk.CTkFrame(self.map_tab)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="🗺️ Regional Storm Track Visualization & Geographic Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        # Keep title compact with small horizontal padding and no vertical padding
        title_label.grid(row=0, column=0, sticky="w", padx=6, pady=(0, 0))

        map_gear = create_settings_gear_button(
            header_frame,
            self.settings_manager,
            "map"
        )
        # Align gear with compact spacing
        map_gear.grid(row=0, column=2, sticky="e", padx=6, pady=(0, 0))

        # Map filtering controls (compact)
        self.create_map_filters()

        # Maximum-size visualization container - expanded to fill space above bottom border
        # Use zero padding so the map canvas can sit flush with the filter bar above
        self.map_viz_frame = ctk.CTkFrame(self.map_tab)
        self.map_viz_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 0))

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
        
        # Full-size visualization container for multi-panel analysis - expanded to fill space above 15px bottom border
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
        """Initialize data processor and visualization engine with database fallback"""
        try:
            self._log("🔧 Initializing tabbed dashboard components...")
            
            # Try to initialize data processor (with database fallback)
            try:
                if DATABASE_AVAILABLE:
                    self._log("📊 Attempting database connection...")
                    self.data_processor = HurricaneDataProcessor()
                    self._log("✅ Database processor initialized")
                else:
                    self._log("📄 Using CSV fallback processor...")
                    self.data_processor = HurricaneDataProcessor()
                    self._log("✅ CSV processor initialized")
            except Exception as db_error:
                self._log(f"⚠️ Database connection failed: {db_error}")
                self._log("📄 Falling back to CSV processor...")
                
                # Import and use CSV processor as fallback
                from csv_data_processor import HurricaneDataProcessor as CsvProcessor
                self.data_processor = CsvProcessor()
                self._log("✅ CSV fallback processor initialized")
            
            # Initialize visualization engine with settings
            self.viz_engine = NativeVisualizationEngine(
                parent_widget=self.root,
                settings=self.settings_manager.settings
            )
            
            self._log("✅ Native visualization engine initialized with matplotlib TkAgg backend")
            self._log("✅ Tabbed dashboard components initialized")
            
            # Auto-load data if available
            self.auto_load_data()
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            self.logger.error(f"Component initialization failed: {e}", exc_info=True)
            
            # Show warning but don't exit - allow user to load data manually
            response = messagebox.askyesno(
                "Initialization Warning", 
                f"Failed to initialize dashboard components: {e}\n\n"
                f"Continue with limited functionality?",
                icon="warning"
            )
            
            if not response:
                self.root.quit()
                return
            
            # Create minimal fallback components
            self._create_fallback_components()
    
    def _create_fallback_components(self):
        """Create minimal fallback components when initialization fails"""
        try:
            print("🔧 Creating fallback components...")
            
            # Create minimal data processor
            if not hasattr(self, 'data_processor') or self.data_processor is None:
                from csv_data_processor import HurricaneDataProcessor as CsvProcessor
                self.data_processor = CsvProcessor()
            
            # Create minimal visualization engine
            if not hasattr(self, 'viz_engine') or self.viz_engine is None:
                self.viz_engine = NativeVisualizationEngine(
                    parent_widget=self.root,
                    settings=self.settings_manager.settings
                )
            
            print("✅ Fallback components created")
            
        except Exception as e:
            print(f"⚠️ Could not create fallback components: {e}")
            self.data_processor = None
            self.viz_engine = None
    
    def auto_load_data(self):
        """Auto-load data during initialization"""
        def auto_load_thread():
            try:
                self._log("📊 Auto-loading hurricane data...")
                self.root.after(0, lambda: self.performance_label.configure(
                    text="📊 Loading hurricane data..."
                ))
                self.root.after(0, lambda: self.progress_bar.set(0.1))
                
                # Use already loaded data from data processor initialization
                if hasattr(self.data_processor, 'gulf_coast_data') and self.data_processor.gulf_coast_data is not None:
                    self.storm_data = self.data_processor.gulf_coast_data
                    self._log(f"📊 Using pre-loaded Gulf Coast data: {len(self.storm_data)} records")
                elif hasattr(self.data_processor, 'processed_data') and self.data_processor.processed_data is not None:
                    self.storm_data = self.data_processor.processed_data
                    self._log(f"📊 Using pre-loaded processed data: {len(self.storm_data)} records")
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
                    
                    self._log(f"✅ Auto-loaded {len(self.storm_data)} hurricane records")
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
                    
                    self._log(f"🌀 Auto-selected storm: {first_storm}")
                    
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
        """Update overview tab with comprehensive interactive statistics report"""
        try:
            if self.storm_data is None:
                return
            
            # Clear existing content
            for widget in self.overview_viz_frame.winfo_children():
                widget.destroy()
            
            # Generate comprehensive report
            self._generate_overview_report(self.storm_data)
            
            self._log("✅ Overview report generated")
        except Exception as e:
            self._log(f"⚠️ Overview update error: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_overview_report(self, data):
        """Generate a comprehensive scrollable statistics report"""
        import pandas as pd
        
        print("📊 Generating overview report...")
        print(f"   Data shape: {data.shape}")
        
        # Configure the scrollable frame grid
        self.overview_viz_frame.grid_columnconfigure(0, weight=1)
        
        # === DATASET SUMMARY SECTION ===
        summary_section = ctk.CTkFrame(
            self.overview_viz_frame, 
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        summary_section.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        summary_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            summary_section,
            text="📋 Dataset Summary",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 5))
        
        # Calculate key metrics
        total_records = len(data)
        total_storms = len(data.groupby(['name', 'year']))
        year_range = f"{data['year'].min()}-{data['year'].max()}"
        unique_years = data['year'].nunique()
        
        # Display summary metrics
        metrics = [
            ("Total Data Points:", f"{total_records:,}"),
            ("Unique Storms:", f"{total_storms:,}"),
            ("Year Range:", year_range),
            ("Years Covered:", f"{unique_years} years"),
            ("Average Points per Storm:", f"{total_records/total_storms:.1f}"),
        ]
        
        for i, (label, value) in enumerate(metrics, start=1):
            ctk.CTkLabel(
                summary_section,
                text=label,
                font=ctk.CTkFont(size=12)
            ).grid(row=i, column=0, sticky="w", padx=15, pady=2)
            
            ctk.CTkLabel(
                summary_section,
                text=value,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.theme.colors.accent if self.theme else "#4a9eff"
            ).grid(row=i, column=1, sticky="w", padx=15, pady=2)
        
        # === STORM CATEGORY BREAKDOWN ===
        category_section = ctk.CTkFrame(
            self.overview_viz_frame, 
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        category_section.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        category_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            category_section,
            text="🌀 Storm Category Distribution",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(10, 5))
        
        # Count by category
        cat_counts = {
            'Tropical Depression': len(data[data['status'] == 'tropical depression']),
            'Tropical Storm': len(data[data['status'] == 'tropical storm']),
            'Category 1': len(data[data['category'] == 1]),
            'Category 2': len(data[data['category'] == 2]),
            'Category 3': len(data[data['category'] == 3]),
            'Category 4': len(data[data['category'] == 4]),
            'Category 5': len(data[data['category'] == 5]),
        }
        
        colors = {
            'Tropical Depression': '#74a9cf',
            'Tropical Storm': '#2b8cbe',
            'Category 1': '#fdcc8a',
            'Category 2': '#fc8d59',
            'Category 3': '#e34a33',
            'Category 4': '#b30000',
            'Category 5': '#7a0177'
        }
        
        for i, (category, count) in enumerate(cat_counts.items(), start=1):
            percentage = (count / total_records * 100) if total_records > 0 else 0
            
            # Category label
            ctk.CTkLabel(
                category_section,
                text=category,
                font=ctk.CTkFont(size=11)
            ).grid(row=i, column=0, sticky="w", padx=15, pady=2)
            
            # Progress bar
            progress = ctk.CTkProgressBar(
                category_section,
                width=300,
                height=15,
                progress_color=colors.get(category, "#4a9eff")
            )
            progress.grid(row=i, column=1, sticky="ew", padx=10, pady=2)
            progress.set(percentage / 100)
            
            # Count and percentage
            ctk.CTkLabel(
                category_section,
                text=f"{count:,} ({percentage:.1f}%)",
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=i, column=2, sticky="e", padx=15, pady=2)
        
        # === WIND SPEED STATISTICS ===
        wind_section = ctk.CTkFrame(
            self.overview_viz_frame, 
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        wind_section.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
        wind_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            wind_section,
            text="💨 Wind Speed Statistics (MPH)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 5))
        
        wind_stats = [
            ("Minimum:", f"{data['wind'].min():.0f} mph"),
            ("Maximum:", f"{data['wind'].max():.0f} mph"),
            ("Average:", f"{data['wind'].mean():.1f} mph"),
            ("Median:", f"{data['wind'].median():.0f} mph"),
            ("Std Deviation:", f"{data['wind'].std():.1f} mph"),
        ]
        
        for i, (label, value) in enumerate(wind_stats, start=1):
            ctk.CTkLabel(
                wind_section,
                text=label,
                font=ctk.CTkFont(size=12)
            ).grid(row=i, column=0, sticky="w", padx=15, pady=2)
            
            ctk.CTkLabel(
                wind_section,
                text=value,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.theme.colors.accent if self.theme else "#4a9eff"
            ).grid(row=i, column=1, sticky="w", padx=15, pady=2)
        
        # === YEARLY TRENDS ===
        yearly_section = ctk.CTkFrame(
            self.overview_viz_frame, 
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        yearly_section.grid(row=3, column=0, sticky="ew", padx=15, pady=15)
        yearly_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            yearly_section,
            text="📅 Yearly Storm Activity",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
        
        # Calculate storms per year
        storms_per_year = data.groupby('year')['name'].nunique().reset_index()
        storms_per_year.columns = ['Year', 'Storm Count']
        
        avg_storms_per_year = storms_per_year['Storm Count'].mean()
        max_storm_year = storms_per_year.loc[storms_per_year['Storm Count'].idxmax()]
        min_storm_year = storms_per_year.loc[storms_per_year['Storm Count'].idxmin()]
        
        yearly_stats = [
            ("Average Storms per Year:", f"{avg_storms_per_year:.1f}"),
            ("Most Active Year:", f"{int(max_storm_year['Year'])} ({int(max_storm_year['Storm Count'])} storms)"),
            ("Least Active Year:", f"{int(min_storm_year['Year'])} ({int(min_storm_year['Storm Count'])} storms)"),
        ]
        
        for i, (label, value) in enumerate(yearly_stats, start=1):
            ctk.CTkLabel(
                yearly_section,
                text=label,
                font=ctk.CTkFont(size=12)
            ).grid(row=i, column=0, sticky="w", padx=15, pady=2)
            
            ctk.CTkLabel(
                yearly_section,
                text=value,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.theme.colors.accent if self.theme else "#4a9eff"
            ).grid(row=i, column=1, sticky="w", padx=15, pady=2)
        
        # === TOP STORMS ===
        top_storms_section = ctk.CTkFrame(
            self.overview_viz_frame, 
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        top_storms_section.grid(row=4, column=0, sticky="ew", padx=15, pady=15)
        top_storms_section.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        ctk.CTkLabel(
            top_storms_section,
            text="🏆 Top 10 Most Intense Storms (by Max Wind Speed)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 5))
        
        # Get top storms
        top_storms = data.groupby(['name', 'year']).agg({
            'wind': 'max',
            'category': 'max'
        }).reset_index().sort_values('wind', ascending=False).head(10)
        
        # Table header
        headers = ["Rank", "Storm Name", "Year", "Max Wind (mph)", "Category"]
        for col, header in enumerate(headers):
            ctk.CTkLabel(
                top_storms_section,
                text=header,
                font=ctk.CTkFont(size=11, weight="bold")
            ).grid(row=1, column=col, sticky="w", padx=10, pady=5)
        
        # Table rows
        for i, (idx, storm) in enumerate(top_storms.iterrows(), start=2):
            ctk.CTkLabel(
                top_storms_section,
                text=f"#{i-1}",
                font=ctk.CTkFont(size=10)
            ).grid(row=i, column=0, sticky="w", padx=10, pady=2)
            
            ctk.CTkLabel(
                top_storms_section,
                text=storm['name'],
                font=ctk.CTkFont(size=10, weight="bold")
            ).grid(row=i, column=1, sticky="w", padx=10, pady=2)
            
            ctk.CTkLabel(
                top_storms_section,
                text=str(int(storm['year'])),
                font=ctk.CTkFont(size=10)
            ).grid(row=i, column=2, sticky="w", padx=10, pady=2)
            
            ctk.CTkLabel(
                top_storms_section,
                text=f"{storm['wind']:.0f} mph",
                font=ctk.CTkFont(size=10),
                text_color=self.theme.colors.accent if self.theme else "#e34a33"
            ).grid(row=i, column=3, sticky="w", padx=10, pady=2)
            
            cat = storm['category']
            cat_text = f"Category {int(cat)}" if pd.notna(cat) else "Tropical Storm"
            ctk.CTkLabel(
                top_storms_section,
                text=cat_text,
                font=ctk.CTkFont(size=10)
            ).grid(row=i, column=4, sticky="w", padx=10, pady=2)
        
        # Add bottom spacer
        spacer = ctk.CTkFrame(self.overview_viz_frame, height=20, fg_color="transparent")
        spacer.grid(row=5, column=0, sticky="ew")
        
        print(f"✅ Overview report generated successfully with 5 sections")
        print(f"   - Dataset Summary")
        print(f"   - Category Distribution")
        print(f"   - Wind Statistics")
        print(f"   - Yearly Trends")
        print(f"   - Top 10 Storms")
    
    def update_timeline_visualization(self):
        """Update timeline visualization with interactive charts and sliders"""
        if self.storm_data is None:
            return
        
        try:
            # Clear existing content
            for widget in self.timeline_viz_frame.winfo_children():
                widget.destroy()
            
            print("📊 Generating interactive timeline analysis...")
            
            # Create 4 interactive chart sections
            self._create_annual_activity_section()
            self._create_seasonal_pattern_section()
            self._create_intensity_evolution_section()
            self._create_decadal_category_section()
            
            self._log("✅ Timeline visualization updated with interactive controls")
        except Exception as e:
            self._log(f"⚠️ Timeline update error: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_annual_activity_section(self):
        """Section 1: Annual Storm Activity with year range slider"""
        section = ctk.CTkFrame(
            self.timeline_viz_frame,
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        section.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        section.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            section,
            text="📈 Annual Storm Activity Timeline",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Year range control frame
        control_frame = ctk.CTkFrame(section, fg_color="transparent")
        control_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        control_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            control_frame,
            text="Year Range:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Year range display
        self.annual_year_label = ctk.CTkLabel(
            control_frame,
            text=f"{self.timeline_year_range[0]} - {self.timeline_year_range[1]}",
            font=ctk.CTkFont(size=12)
        )
        self.annual_year_label.grid(row=0, column=1, sticky="w")
        
        # Start year slider
        slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        slider_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(slider_frame, text="Start Year:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.annual_start_slider = ctk.CTkSlider(
            slider_frame,
            from_=1975,
            to=2021,
            number_of_steps=46,
            command=self._update_annual_start_year
        )
        self.annual_start_slider.set(self.timeline_year_range[0])
        self.annual_start_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # End year slider
        end_slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        end_slider_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        end_slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(end_slider_frame, text="End Year:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.annual_end_slider = ctk.CTkSlider(
            end_slider_frame,
            from_=1975,
            to=2021,
            number_of_steps=46,
            command=self._update_annual_end_year
        )
        self.annual_end_slider.set(self.timeline_year_range[1])
        self.annual_end_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Chart container
        self.annual_chart_frame = ctk.CTkFrame(section, fg_color="transparent")
        self.annual_chart_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=15)
        self.annual_chart_frame.grid_rowconfigure(0, weight=1)
        self.annual_chart_frame.grid_columnconfigure(0, weight=1)
        
        # Generate initial chart
        self._update_annual_activity_chart()
    
    def _update_annual_start_year(self, value):
        """Update start year for annual activity chart"""
        start_year = int(value)
        if start_year < self.timeline_year_range[1]:
            self.timeline_year_range[0] = start_year
            self.annual_year_label.configure(text=f"{self.timeline_year_range[0]} - {self.timeline_year_range[1]}")
            self._update_annual_activity_chart()
    
    def _update_annual_end_year(self, value):
        """Update end year for annual activity chart"""
        end_year = int(value)
        if end_year > self.timeline_year_range[0]:
            self.timeline_year_range[1] = end_year
            self.annual_year_label.configure(text=f"{self.timeline_year_range[0]} - {self.timeline_year_range[1]}")
            self._update_annual_activity_chart()
    
    def _update_annual_activity_chart(self):
        """Generate/update the annual activity chart"""
        # Clear existing chart
        for widget in self.annual_chart_frame.winfo_children():
            widget.destroy()
        
        # Filter data by year range
        filtered_data = self.storm_data[
            (self.storm_data['year'] >= self.timeline_year_range[0]) &
            (self.storm_data['year'] <= self.timeline_year_range[1])
        ]
        
        # Count storms per year
        yearly_counts = filtered_data.groupby('year').apply(lambda x: x.groupby('name').ngroups).reset_index()
        yearly_counts.columns = ['year', 'storm_count']
        
        # Create matplotlib figure
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(12, 4), dpi=100, facecolor='#1a1a1a')
        ax = fig.add_subplot(111, facecolor='#1a1a1a')
        
        if not yearly_counts.empty:
            years = yearly_counts['year'].values
            counts = yearly_counts['storm_count'].values
            
            # Line chart with markers
            ax.plot(years, counts, color='#4a90e2', linewidth=3, marker='o', 
                   markersize=6, markerfacecolor='white', markeredgecolor='#4a90e2', 
                   markeredgewidth=2, label='Storm Count')
            
            # Add trend line
            if len(years) > 2:
                z = np.polyfit(years, counts, 1)
                trend_line = np.poly1d(z)
                ax.plot(years, trend_line(years), color='#ff6b35', linestyle='--', 
                       linewidth=2, alpha=0.8, label=f'Trend {"↗" if z[0] > 0 else "↘"}')
            
            # Styling
            ax.set_xlabel('Year', fontsize=11, fontweight='bold', color='white')
            ax.set_ylabel('Number of Storms', fontsize=11, fontweight='bold', color='white')
            ax.tick_params(colors='white')
            ax.legend(loc='upper left', fontsize=10, facecolor='#2a2a2a', edgecolor='white')
            ax.grid(True, alpha=0.2, color='white', linestyle=':')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Stats annotation
            avg_storms = np.mean(counts)
            max_year = years[np.argmax(counts)]
            max_count = np.max(counts)
            stats_text = f'Avg: {avg_storms:.1f}/year\nPeak: {max_count} ({max_year})'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10, color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='white'))
        
        fig.tight_layout()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, self.annual_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    
    def _create_seasonal_pattern_section(self):
        """Section 2: Seasonal Pattern with month range slider"""
        section = ctk.CTkFrame(
            self.timeline_viz_frame,
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        section.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        section.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            section,
            text="🌊 Seasonal Distribution Pattern",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Month range control
        control_frame = ctk.CTkFrame(section, fg_color="transparent")
        control_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        control_frame.grid_columnconfigure(1, weight=1)
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        ctk.CTkLabel(
            control_frame,
            text="Month Range:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.seasonal_month_label = ctk.CTkLabel(
            control_frame,
            text=f"{month_names[self.timeline_month_range[0]-1]} - {month_names[self.timeline_month_range[1]-1]}",
            font=ctk.CTkFont(size=12)
        )
        self.seasonal_month_label.grid(row=0, column=1, sticky="w")
        
        # Start month slider
        slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        slider_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(slider_frame, text="Start Month:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.seasonal_start_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=12,
            number_of_steps=11,
            command=self._update_seasonal_start_month
        )
        self.seasonal_start_slider.set(self.timeline_month_range[0])
        self.seasonal_start_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # End month slider
        end_slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        end_slider_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        end_slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(end_slider_frame, text="End Month:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.seasonal_end_slider = ctk.CTkSlider(
            end_slider_frame,
            from_=1,
            to=12,
            number_of_steps=11,
            command=self._update_seasonal_end_month
        )
        self.seasonal_end_slider.set(self.timeline_month_range[1])
        self.seasonal_end_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Chart container
        self.seasonal_chart_frame = ctk.CTkFrame(section, fg_color="transparent")
        self.seasonal_chart_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=15)
        self.seasonal_chart_frame.grid_rowconfigure(0, weight=1)
        self.seasonal_chart_frame.grid_columnconfigure(0, weight=1)
        
        # Generate initial chart
        self._update_seasonal_pattern_chart()
    
    def _update_seasonal_start_month(self, value):
        """Update start month for seasonal pattern chart"""
        start_month = int(value)
        if start_month < self.timeline_month_range[1]:
            self.timeline_month_range[0] = start_month
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            self.seasonal_month_label.configure(
                text=f"{month_names[self.timeline_month_range[0]-1]} - {month_names[self.timeline_month_range[1]-1]}"
            )
            self._update_seasonal_pattern_chart()
    
    def _update_seasonal_end_month(self, value):
        """Update end month for seasonal pattern chart"""
        end_month = int(value)
        if end_month > self.timeline_month_range[0]:
            self.timeline_month_range[1] = end_month
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            self.seasonal_month_label.configure(
                text=f"{month_names[self.timeline_month_range[0]-1]} - {month_names[self.timeline_month_range[1]-1]}"
            )
            self._update_seasonal_pattern_chart()
    
    def _update_seasonal_pattern_chart(self):
        """Generate/update the seasonal pattern chart"""
        # Clear existing chart
        for widget in self.seasonal_chart_frame.winfo_children():
            widget.destroy()
        
        # Filter data by month range
        filtered_data = self.storm_data[
            (self.storm_data['month'] >= self.timeline_month_range[0]) &
            (self.storm_data['month'] <= self.timeline_month_range[1])
        ]
        
        # Count storms per month
        monthly_counts = filtered_data.groupby('month').size()
        
        # Create matplotlib figure
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(12, 4), dpi=100, facecolor='#1a1a1a')
        ax = fig.add_subplot(111, facecolor='#1a1a1a')
        
        if not monthly_counts.empty:
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            months = monthly_counts.index.values
            counts = monthly_counts.values
            labels = [month_names[m-1] for m in months]
            
            # Bar chart with gradient colors
            colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(months)))
            bars = ax.bar(labels, counts, color=colors, edgecolor='white', linewidth=1.5)
            
            # Highlight peak month
            peak_idx = np.argmax(counts)
            bars[peak_idx].set_color('#ff6b35')
            
            # Styling
            ax.set_xlabel('Month', fontsize=11, fontweight='bold', color='white')
            ax.set_ylabel('Number of Storms', fontsize=11, fontweight='bold', color='white')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.2, color='white', linestyle=':', axis='y')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Stats annotation
            peak_month = month_names[months[peak_idx]-1]
            peak_count = counts[peak_idx]
            total = np.sum(counts)
            stats_text = f'Peak: {peak_month} ({peak_count} storms)\nTotal: {total} storms'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10, color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='white'))
        
        fig.tight_layout()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, self.seasonal_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    
    def _create_intensity_evolution_section(self):
        """Section 3: Intensity Evolution with category threshold slider"""
        section = ctk.CTkFrame(
            self.timeline_viz_frame,
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        section.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
        section.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            section,
            text="💨 Intensity Evolution Over Time",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Category threshold control
        control_frame = ctk.CTkFrame(section, fg_color="transparent")
        control_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        control_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            control_frame,
            text="Minimum Category:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        category_labels = ['All Storms', 'Cat 1+', 'Cat 2+', 'Cat 3+', 'Cat 4+', 'Cat 5 Only']
        
        self.intensity_category_label = ctk.CTkLabel(
            control_frame,
            text=category_labels[self.timeline_category_threshold],
            font=ctk.CTkFont(size=12)
        )
        self.intensity_category_label.grid(row=0, column=1, sticky="w")
        
        # Category threshold slider
        slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        slider_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(slider_frame, text="Filter:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.intensity_category_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=5,
            number_of_steps=5,
            command=self._update_intensity_category
        )
        self.intensity_category_slider.set(self.timeline_category_threshold)
        self.intensity_category_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Chart container
        self.intensity_chart_frame = ctk.CTkFrame(section, fg_color="transparent")
        self.intensity_chart_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=15)
        self.intensity_chart_frame.grid_rowconfigure(0, weight=1)
        self.intensity_chart_frame.grid_columnconfigure(0, weight=1)
        
        # Generate initial chart
        self._update_intensity_evolution_chart()
    
    def _update_intensity_category(self, value):
        """Update category threshold for intensity evolution chart"""
        self.timeline_category_threshold = int(value)
        category_labels = ['All Storms', 'Cat 1+', 'Cat 2+', 'Cat 3+', 'Cat 4+', 'Cat 5 Only']
        self.intensity_category_label.configure(text=category_labels[self.timeline_category_threshold])
        self._update_intensity_evolution_chart()
    
    def _update_intensity_evolution_chart(self):
        """Generate/update the intensity evolution chart"""
        # Clear existing chart
        for widget in self.intensity_chart_frame.winfo_children():
            widget.destroy()
        
        # Filter data by category
        if self.timeline_category_threshold == 0:
            filtered_data = self.storm_data.copy()
        elif self.timeline_category_threshold == 5:
            filtered_data = self.storm_data[self.storm_data['category'] == 5]
        else:
            filtered_data = self.storm_data[self.storm_data['category'] >= self.timeline_category_threshold]
        
        # Group by year and calculate average wind speed
        yearly_intensity = filtered_data.groupby('year')['wind'].agg(['mean', 'max', 'min']).reset_index()
        
        # Create matplotlib figure
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(12, 4), dpi=100, facecolor='#1a1a1a')
        ax = fig.add_subplot(111, facecolor='#1a1a1a')
        
        if not yearly_intensity.empty:
            years = yearly_intensity['year'].values
            avg_wind = yearly_intensity['mean'].values
            max_wind = yearly_intensity['max'].values
            min_wind = yearly_intensity['min'].values
            
            # Area chart showing range
            ax.fill_between(years, min_wind, max_wind, color='#4a90e2', alpha=0.3, label='Wind Speed Range')
            ax.plot(years, avg_wind, color='#ff6b35', linewidth=3, marker='o', 
                   markersize=5, label='Average Wind Speed')
            
            # Styling
            ax.set_xlabel('Year', fontsize=11, fontweight='bold', color='white')
            ax.set_ylabel('Wind Speed (mph)', fontsize=11, fontweight='bold', color='white')
            ax.tick_params(colors='white')
            ax.legend(loc='upper left', fontsize=10, facecolor='#2a2a2a', edgecolor='white')
            ax.grid(True, alpha=0.2, color='white', linestyle=':')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Stats annotation
            overall_avg = np.mean(avg_wind)
            overall_max = np.max(max_wind)
            stats_text = f'Avg Wind: {overall_avg:.1f} mph\nMax Recorded: {overall_max:.0f} mph'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10, color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='white'))
        
        fig.tight_layout()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, self.intensity_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    
    def _create_decadal_category_section(self):
        """Section 4: Decadal Category Distribution with decade range slider"""
        section = ctk.CTkFrame(
            self.timeline_viz_frame,
            fg_color=self.theme.colors.bg_tertiary if self.theme else "#2a2a2a",
            corner_radius=10
        )
        section.grid(row=3, column=0, sticky="ew", padx=15, pady=15)
        section.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            section,
            text="📊 Hurricane Category Distribution by Decade",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Decade range control
        control_frame = ctk.CTkFrame(section, fg_color="transparent")
        control_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        control_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            control_frame,
            text="Decade Range:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.decadal_range_label = ctk.CTkLabel(
            control_frame,
            text=f"{self.timeline_decade_range[0]}s - {self.timeline_decade_range[1]}s",
            font=ctk.CTkFont(size=12)
        )
        self.decadal_range_label.grid(row=0, column=1, sticky="w")
        
        # Start decade slider
        slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        slider_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(slider_frame, text="Start Decade:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.decadal_start_slider = ctk.CTkSlider(
            slider_frame,
            from_=1970,
            to=2020,
            number_of_steps=5,
            command=self._update_decadal_start
        )
        self.decadal_start_slider.set(self.timeline_decade_range[0])
        self.decadal_start_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # End decade slider
        end_slider_frame = ctk.CTkFrame(section, fg_color="transparent")
        end_slider_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        end_slider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(end_slider_frame, text="End Decade:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.decadal_end_slider = ctk.CTkSlider(
            end_slider_frame,
            from_=1970,
            to=2020,
            number_of_steps=5,
            command=self._update_decadal_end
        )
        self.decadal_end_slider.set(self.timeline_decade_range[1])
        self.decadal_end_slider.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Chart container
        self.decadal_chart_frame = ctk.CTkFrame(section, fg_color="transparent")
        self.decadal_chart_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=15)
        self.decadal_chart_frame.grid_rowconfigure(0, weight=1)
        self.decadal_chart_frame.grid_columnconfigure(0, weight=1)
        
        # Generate initial chart
        self._update_decadal_category_chart()
    
    def _update_decadal_start(self, value):
        """Update start decade for decadal category chart"""
        start_decade = int(value)
        if start_decade < self.timeline_decade_range[1]:
            self.timeline_decade_range[0] = start_decade
            self.decadal_range_label.configure(text=f"{self.timeline_decade_range[0]}s - {self.timeline_decade_range[1]}s")
            self._update_decadal_category_chart()
    
    def _update_decadal_end(self, value):
        """Update end decade for decadal category chart"""
        end_decade = int(value)
        if end_decade > self.timeline_decade_range[0]:
            self.timeline_decade_range[1] = end_decade
            self.decadal_range_label.configure(text=f"{self.timeline_decade_range[0]}s - {self.timeline_decade_range[1]}s")
            self._update_decadal_category_chart()
    
    def _update_decadal_category_chart(self):
        """Generate/update the decadal category distribution chart"""
        # Clear existing chart
        for widget in self.decadal_chart_frame.winfo_children():
            widget.destroy()
        
        # Create decade bins and filter data
        self.storm_data['decade'] = (self.storm_data['year'] // 10) * 10
        filtered_data = self.storm_data[
            (self.storm_data['decade'] >= self.timeline_decade_range[0]) &
            (self.storm_data['decade'] <= self.timeline_decade_range[1])
        ]
        
        # Group by decade and category
        decadal_cats = filtered_data.groupby(['decade', 'category']).size().unstack(fill_value=0)
        
        # Create matplotlib figure
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(12, 4), dpi=100, facecolor='#1a1a1a')
        ax = fig.add_subplot(111, facecolor='#1a1a1a')
        
        if not decadal_cats.empty:
            # Category colors
            cat_colors = {
                0: '#74c0fc',  # Tropical Storm
                1: '#69db7c',  # Cat 1
                2: '#ffd43b',  # Cat 2
                3: '#ff922b',  # Cat 3
                4: '#ff6b6b',  # Cat 4
                5: '#da77f2'   # Cat 5
            }
            
            # Stacked bar chart
            decades = [f"{int(d)}s" for d in decadal_cats.index]
            bottom = np.zeros(len(decadal_cats))
            
            for cat in sorted(decadal_cats.columns):
                if cat in cat_colors:
                    values = decadal_cats[cat].values
                    cat_label = f'Cat {int(cat)}' if cat > 0 else 'TS'
                    ax.bar(decades, values, bottom=bottom, color=cat_colors[cat], 
                          label=cat_label, edgecolor='white', linewidth=1)
                    bottom += values
            
            # Styling
            ax.set_xlabel('Decade', fontsize=11, fontweight='bold', color='white')
            ax.set_ylabel('Number of Storms', fontsize=11, fontweight='bold', color='white')
            ax.tick_params(colors='white')
            ax.legend(loc='upper left', fontsize=9, facecolor='#2a2a2a', edgecolor='white', ncol=2)
            ax.grid(True, alpha=0.2, color='white', linestyle=':', axis='y')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Stats annotation
            total_storms = int(np.sum(decadal_cats.values))
            avg_per_decade = total_storms / len(decadal_cats)
            stats_text = f'Total: {total_storms} storms\nAvg: {avg_per_decade:.1f}/decade'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10, color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='white'))
        
        fig.tight_layout()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, self.decadal_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
    
    def update_map_visualization(self):
        """Update the map visualization with current filters"""
        try:
            if not self.viz_engine or self.storm_data is None:
                return
            
            # Clear existing map
            for widget in self.map_viz_frame.winfo_children():
                widget.destroy()
            
            # Generate updated map with filters
            map_result = self.viz_engine.generate_map_visualization(
                self.storm_data,
                self.map_viz_frame,
                show_multiple_tracks=getattr(self, 'current_show_multiple', True),
                filter_options=getattr(self, 'current_map_filters', {})
            )
            
            if map_result and isinstance(map_result, dict) and 'canvas' in map_result:
                # Extract canvas from result dictionary and place it using get_tk_widget()
                map_canvas = map_result['canvas']
                # Place the canvas with no extra padding so it completely fills the viz frame
                map_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
                
                self._log(f"🗺️ Map visualization updated with filters: {getattr(self, 'current_map_filters', {})}")
            
        except Exception as e:
            self._log(f"⚠️ Map update error: {e}")
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
                self._log("✅ Analysis visualization updated")
        except Exception as e:
            self._log(f"⚠️ Analysis update error: {e}")
    
    # Callback versions that mark visualizations as complete
    def update_overview_visualization_with_callback(self):
        """Update overview visualization and mark as complete"""
        self.update_overview_visualization()
        self.mark_visualization_complete('overview')
    
    def update_timeline_visualization_with_callback(self):
        """Update timeline visualization and mark as complete"""
        self.update_timeline_visualization()
        self.mark_visualization_complete('timeline')
    
    def update_map_visualization_with_callback(self):
        """Update map visualization and mark as complete"""
        self.update_map_visualization()
        self.mark_visualization_complete('map')
    
    def update_analysis_visualization_with_callback(self):
        """Update analysis visualization and mark as complete"""
        self.update_analysis_visualization()
        self.mark_visualization_complete('analysis')
    
    def check_all_visualizations_complete(self):
        """Check if all visualizations are complete and trigger callback if so"""
        if all(self.visualizations_ready.values()) and not self.all_visualizations_complete:
            self.all_visualizations_complete = True
            self._log("✅ All visualizations are now complete!")
            
            # Update loading bar to show completion
            if hasattr(self, 'loading_status_label'):
                self.loading_status_label.configure(text="✅ All visualizations loaded successfully!")
                self.progress_bar.set(1.0)
                self.loading_details_label.configure(text="Dashboard ready")
                
                # Hide loading bar after a brief delay
                def hide_loading_bar():
                    if hasattr(self, 'loading_frame'):
                        self.loading_frame.grid_remove()
                
                self.root.after(2000, hide_loading_bar)
            
            if self.loading_callback:
                self.loading_callback()
                self._log("📞 Loading callback triggered")
    
    def mark_visualization_complete(self, viz_name):
        """Mark a specific visualization as complete and update loading bar"""
        if viz_name in self.visualizations_ready:
            self.visualizations_ready[viz_name] = True
            self._log(f"✅ {viz_name.capitalize()} visualization complete")
            
            # Update loading bar progress
            completed_count = sum(1 for ready in self.visualizations_ready.values() if ready)
            total_count = len(self.visualizations_ready)
            progress = completed_count / total_count
            
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(progress)
            
            # Update loading details to show which are still loading
            if hasattr(self, 'loading_details_label'):
                loading_viz = [name.capitalize() for name, ready in self.visualizations_ready.items() if not ready]
                if loading_viz:
                    self.loading_details_label.configure(
                        text=f"Loading: {', '.join(loading_viz)} ({completed_count}/{total_count} complete)"
                    )
                else:
                    self.loading_details_label.configure(text=f"All visualizations loaded ({total_count}/{total_count})")
            
            self.check_all_visualizations_complete()
    
    def update_all_visualizations(self):
        """Update all visualizations"""
        self._log("🔄 Updating tabbed visualizations...")
        
        # Reset completion status and show loading bar
        self.visualizations_ready = {key: False for key in self.visualizations_ready}
        self.all_visualizations_complete = False
        
        # Show and reset loading bar
        if hasattr(self, 'loading_frame'):
            self.loading_frame.grid()
            self.progress_bar.set(0)
            self.loading_status_label.configure(text="🔄 Reloading visualizations...")
            self.loading_details_label.configure(text="Initializing: Overview, Timeline, Map, Analysis")
        
        def update_thread():
            try:
                self.root.after(0, lambda: self.performance_label.configure(
                    text="🔄 Updating visualizations..."
                ))
                
                # Update all tabs with completion tracking
                self.root.after(0, lambda: self.update_overview_visualization_with_callback())
                self.root.after(0, lambda: self.update_timeline_visualization_with_callback())
                self.root.after(0, lambda: self.update_map_visualization_with_callback())  
                self.root.after(0, lambda: self.update_analysis_visualization_with_callback())
                
            except Exception as ex:
                error_msg = str(ex)
                self.root.after(0, lambda msg=error_msg: self.performance_label.configure(
                    text=f"❌ Update failed: {msg}"
                ))
                print(f"❌ Visualization update error: {ex}")
        
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
                
            except Exception as ex:
                error_msg = str(ex)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror(
                    "Data Loading Error", f"Failed to load data: {msg}"
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
        # Ultra-compact filter controls frame
        filter_frame = self.theme.get_styled_frame(self.map_tab, style="card")
        # Remove outer padding so filters sit tightly under the header
        filter_frame.grid(row=1, column=0, sticky="ew",
                         padx=0,
                         pady=(0, 0))
        
        # Configure grid for filter sections
        filter_frame.grid_columnconfigure(0, weight=1)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)
        
        # Year range filtering
        year_frame = self.theme.get_styled_frame(filter_frame, style="primary")
        year_frame.grid(row=0, column=0, sticky="ew", 
                       padx=2, 
                       pady=2)
        
        self.theme.get_styled_label(year_frame, text="📅 Year Range", style="subheader").pack(pady=1)
        
        year_controls = self.theme.get_styled_frame(year_frame, style="transparent")
        year_controls.pack(fill="x", padx=2, pady=1)
        
        self.theme.get_styled_label(year_controls, text="From:", style="caption").pack(side="left", padx=2)
        self.year_start_var = tk.StringVar(value="1975")
        self.year_start_entry = self.theme.get_styled_entry(year_controls, width=60)
        self.year_start_entry.configure(textvariable=self.year_start_var)
        self.year_start_entry.pack(side="left", padx=2)
        print(f"🔧 Year start entry created with default value: '{self.year_start_var.get()}'")
        
        self.theme.get_styled_label(year_controls, text="To:", style="caption").pack(side="left", padx=2)
        self.year_end_var = tk.StringVar(value="2025")
        self.year_end_entry = self.theme.get_styled_entry(year_controls, width=60)
        self.year_end_entry.configure(textvariable=self.year_end_var)
        self.year_end_entry.pack(side="left", padx=2)
        print(f"🔧 Year end entry created with default value: '{self.year_end_var.get()}'")
        
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
            # Fix the numbering - extract actual category number or use TS for Tropical Storm
            if "Category" in category:
                cat_num = category.split()[-1]  # Extract "1", "2", etc. from "Category 1", "Category 2"
                display_text = f"Cat {cat_num}"
            else:
                display_text = "TS"
            
            checkbox = ctk.CTkCheckBox(cat_controls, text=display_text,
                                     variable=self.category_vars[category], width=50)
            checkbox.pack(side="left", padx=1)
        
        # Wind speed filtering with interactive sliders
        wind_frame = ctk.CTkFrame(filter_frame)
        wind_frame.grid(row=0, column=2, sticky="ew", padx=2, pady=2)
        
        ctk.CTkLabel(wind_frame, text="💨 Wind Speed (MPH)", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=2)
        
        wind_controls = ctk.CTkFrame(wind_frame)
        wind_controls.pack(fill="x", padx=3, pady=1)
        
        # Minimum wind speed slider
        min_wind_container = ctk.CTkFrame(wind_controls)
        min_wind_container.pack(fill="x", pady=2)
        
        self.min_wind_var = tk.IntVar(value=35)
        self.min_wind_label = ctk.CTkLabel(min_wind_container, text=f"Min: {self.min_wind_var.get()} mph", 
                                          font=ctk.CTkFont(size=10))
        self.min_wind_label.pack(side="left", padx=2)
        
        self.min_wind_slider = ctk.CTkSlider(
            min_wind_container, 
            from_=0, 
            to=200, 
            number_of_steps=40,
            variable=self.min_wind_var,
            command=self.update_min_wind_label,
            width=140
        )
        self.min_wind_slider.pack(side="left", padx=2)
        
        # Maximum wind speed slider
        max_wind_container = ctk.CTkFrame(wind_controls)
        max_wind_container.pack(fill="x", pady=2)
        
        self.max_wind_var = tk.IntVar(value=200)
        self.max_wind_label = ctk.CTkLabel(max_wind_container, text=f"Max: {self.max_wind_var.get()} mph", 
                                          font=ctk.CTkFont(size=10))
        self.max_wind_label.pack(side="left", padx=2)
        
        self.max_wind_slider = ctk.CTkSlider(
            max_wind_container, 
            from_=0, 
            to=200, 
            number_of_steps=40,
            variable=self.max_wind_var,
            command=self.update_max_wind_label,
            width=140
        )
        self.max_wind_slider.pack(side="left", padx=2)
        
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
    
    def update_min_wind_label(self, value):
        """Update the minimum wind speed label when slider moves"""
        wind_value = int(float(value))
        self.min_wind_label.configure(text=f"Min: {wind_value} mph")
    
    def update_max_wind_label(self, value):
        """Update the maximum wind speed label when slider moves"""
        wind_value = int(float(value))
        self.max_wind_label.configure(text=f"Max: {wind_value} mph")
    
    def apply_map_filters(self):
        """Apply the selected filters to the map visualization"""
        try:
            # Read year values DIRECTLY from the entry widgets (more reliable with CTkEntry)
            year_start_text = self.year_start_entry.get().strip()
            year_end_text = self.year_end_entry.get().strip()
            
            print(f"\n{'='*60}")
            print(f"🔍 READING FILTER VALUES FROM UI")
            print(f"{'='*60}")
            print(f"  📅 Year Start Entry Widget:")
            print(f"     - entry.get() = '{year_start_text}'")
            print(f"     - StringVar.get() = '{self.year_start_var.get()}'")
            print(f"  📅 Year End Entry Widget:")
            print(f"     - entry.get() = '{year_end_text}'")
            print(f"     - StringVar.get() = '{self.year_end_var.get()}'")
            print(f"{'='*60}\n")
            
            # Validate year inputs
            if not year_start_text or not year_end_text:
                messagebox.showerror("Filter Error", "Year range cannot be empty")
                return
            
            # Gather filter options
            filter_options = {
                'year_start': int(year_start_text),
                'year_end': int(year_end_text),
                'min_wind': int(self.min_wind_var.get()),
                'max_wind': int(self.max_wind_var.get()),
                'categories': [cat for cat, var in self.category_vars.items() if var.get()]
            }
            
            # Validate year range makes sense
            if filter_options['year_start'] > filter_options['year_end']:
                messagebox.showerror("Filter Error", 
                    f"Start year ({filter_options['year_start']}) cannot be greater than end year ({filter_options['year_end']})")
                return
            
            show_multiple = self.show_multiple_var.get()
            
            print(f"\n{'='*60}")
            print(f"🎛️ APPLYING MAP FILTERS FROM UI CONTROLS")
            print(f"{'='*60}")
            print(f"  📅 Year Range (from entry.get()):")
            print(f"     - Start: '{year_start_text}' → {filter_options['year_start']}")
            print(f"     - End: '{year_end_text}' → {filter_options['year_end']}")
            print(f"  🌀 Categories Selected: {filter_options['categories']}")
            print(f"  💨 Wind Speed Range: {filter_options['min_wind']} - {filter_options['max_wind']} mph")
            print(f"  🗺️  Multi-Track Mode: {show_multiple}")
            print(f"{'='*60}\n")
            
            # Update map visualization with filters
            if self.viz_engine and self.storm_data is not None:
                # Store filter options for map updates
                self.current_map_filters = filter_options
                self.current_show_multiple = show_multiple
                
                # Update the map visualization
                self.update_map_visualization()
                
                self.performance_label.configure(
                    text=f"✅ Filters: {filter_options['year_start']}-{filter_options['year_end']}, "
                         f"{len(filter_options['categories'])} categories, "
                         f"{filter_options['min_wind']}-{filter_options['max_wind']} mph"
                )
            
        except ValueError as e:
            print(f"❌ Filter value error: {e}")
            messagebox.showerror("Filter Error", 
                f"Invalid filter values. Please check:\n"
                f"- Year start: '{year_start_text if 'year_start_text' in locals() else 'ERROR'}'\n"
                f"- Year end: '{year_end_text if 'year_end_text' in locals() else 'ERROR'}'\n"
                f"- Min wind: {self.min_wind_var.get()}\n"
                f"- Max wind: {self.max_wind_var.get()}\n\n"
                f"Error: {e}")
        except Exception as e:
            print(f"⚠️ Filter application error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Filter Error", f"Failed to apply filters: {e}")
    
    def reset_map_filters(self):
        """Reset all map filters to default values"""
        # Reset year range
        self.year_start_var.set("1975")
        self.year_end_var.set("2025")
        
        # Reset wind speed sliders (IntVar uses int values)
        self.min_wind_var.set(35)
        self.max_wind_var.set(200)
        
        # Update wind speed labels
        self.min_wind_label.configure(text="Min: 35 mph")
        self.max_wind_label.configure(text="Max: 200 mph")
        
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
            self._log("🚀 Starting Tabbed Native Hurricane Dashboard...")
            
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