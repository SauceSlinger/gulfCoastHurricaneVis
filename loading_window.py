#!/usr/bin/env python3
"""
Professional Loading Window with Progress Tracking
Shows a beautiful loading screen while the dashboard initializes
"""

import tkinter as tk
from tkinter import ttk
import threading
import time


class LoadingWindow:
    """Professional loading window with progress tracking"""
    
    def __init__(self):
        """Initialize the loading window"""
        self.window = tk.Tk()
        self.window.title("Hurricane Dashboard")
        
        # Window configuration
        window_width = 500
        window_height = 300
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(False, False)
        self.window.configure(bg='#1a1a1a')
        
        # Remove window decorations for a cleaner look
        self.window.overrideredirect(True)
        
        # Loading state
        self.loading_complete = False
        self.current_message = "Initializing..."
        self.progress_value = 0
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the loading window UI"""
        # Main container
        main_frame = tk.Frame(self.window, bg='#1a1a1a', relief=tk.RAISED, borderwidth=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header with icon
        header_frame = tk.Frame(main_frame, bg='#1a1a1a')
        header_frame.pack(pady=(30, 10))
        
        title_label = tk.Label(
            header_frame,
            text="🌀 Hurricane Dashboard",
            font=('Arial', 24, 'bold'),
            fg='#4a9eff',
            bg='#1a1a1a'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Professional Edition",
            font=('Arial', 12),
            fg='#888888',
            bg='#1a1a1a'
        )
        subtitle_label.pack()
        
        # Progress section
        progress_frame = tk.Frame(main_frame, bg='#1a1a1a')
        progress_frame.pack(pady=20, padx=40, fill=tk.X)
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#2a2a2a',
            background='#4a9eff',
            bordercolor='#1a1a1a',
            lightcolor='#4a9eff',
            darkcolor='#4a9eff'
        )
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            mode='determinate',
            length=420,
            maximum=100
        )
        self.progress_bar.pack(pady=10)
        
        # Status message
        self.status_label = tk.Label(
            progress_frame,
            text=self.current_message,
            font=('Arial', 10),
            fg='#cccccc',
            bg='#1a1a1a'
        )
        self.status_label.pack()
        
        # Loading details
        details_frame = tk.Frame(main_frame, bg='#1a1a1a')
        details_frame.pack(pady=10)
        
        self.details_label = tk.Label(
            details_frame,
            text="Setting up environment...",
            font=('Arial', 9),
            fg='#666666',
            bg='#1a1a1a'
        )
        self.details_label.pack()
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg='#1a1a1a')
        footer_frame.pack(side=tk.BOTTOM, pady=10)
        
        footer_label = tk.Label(
            footer_frame,
            text="Please wait while we prepare your dashboard...",
            font=('Arial', 8, 'italic'),
            fg='#555555',
            bg='#1a1a1a'
        )
        footer_label.pack()
        
    def update_progress(self, value, message=None, details=None):
        """Update the progress bar and message"""
        # Check if window still exists
        if not hasattr(self, 'window') or not self.window.winfo_exists():
            return
        
        try:
            self.progress_value = min(value, 100)
            self.progress_bar['value'] = self.progress_value
            
            if message:
                self.current_message = message
                self.status_label.configure(text=message)
            
            if details:
                self.details_label.configure(text=details)
            
            self.window.update()
        except (tk.TclError, AttributeError):
            # Window was destroyed, silently ignore
            pass
        
    def close(self):
        """Close the loading window"""
        self.loading_complete = True
        try:
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.destroy()
        except (tk.TclError, AttributeError):
            # Window already destroyed
            pass


def launch_with_loading_screen():
    """Launch the dashboard with a professional loading screen"""
    
    # Create loading window
    loading = LoadingWindow()
    loading.update_progress(10, "Starting Hurricane Dashboard...", "Importing modules...")
    
    def load_dashboard():
        """Load dashboard in background thread"""
        try:
            # Import dashboard
            loading.update_progress(20, "Loading dependencies...", "Importing libraries...")
            from tabbed_native_dashboard import TabbedNativeDashboard
            
            loading.update_progress(40, "Initializing dashboard...", "Setting up UI components...")
            
            # Create dashboard with loading callback
            def on_loading_complete():
                """Called when all visualizations are ready"""
                loading.update_progress(100, "Complete!", "Dashboard is ready")
                time.sleep(0.5)
                loading.close()
            
            def log_callback(message):
                """Update loading window with log messages"""
                # Parse message for progress updates
                if "Loading data" in message:
                    loading.update_progress(50, "Loading data...", message)
                elif "Creating visualizations" in message or "visualization" in message.lower():
                    loading.update_progress(60, "Creating visualizations...", message)
                elif "Overview" in message:
                    loading.update_progress(70, "Preparing overview...", message)
                elif "Timeline" in message:
                    loading.update_progress(75, "Preparing timeline...", message)
                elif "Map" in message:
                    loading.update_progress(80, "Preparing map...", message)
                elif "Analysis" in message:
                    loading.update_progress(85, "Preparing analysis...", message)
                elif "complete" in message.lower():
                    loading.update_progress(95, "Finalizing...", message)
            
            loading.update_progress(45, "Creating dashboard...", "Building interface...")
            
            # Create dashboard with callbacks
            dashboard = TabbedNativeDashboard(
                loading_callback=on_loading_complete,
                log_callback=log_callback
            )
            
            loading.update_progress(55, "Dashboard created", "Loading interface...")
            
            # Close loading window after a brief delay to ensure dashboard is visible
            def delayed_close():
                time.sleep(1)
                if not loading.loading_complete:
                    loading.close()
            
            # Start dashboard
            loading.window.after(500, lambda: threading.Thread(target=delayed_close, daemon=True).start())
            dashboard.run()
            
        except Exception as e:
            print(f"❌ Failed to launch dashboard: {e}")
            import traceback
            traceback.print_exc()
            loading.update_progress(0, "Error occurred", str(e))
            time.sleep(3)
            loading.close()
    
    # Start loading in main thread
    loading.window.after(100, load_dashboard)
    
    # Run loading window
    loading.window.mainloop()


if __name__ == "__main__":
    launch_with_loading_screen()
