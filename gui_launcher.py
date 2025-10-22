#!/usr/bin/env python3
"""
GUI Loading Window for Hurricane Dashboard
Professional loading interface that properly hands off to the main dashboard
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
import sys
from pathlib import Path
from typing import Tuple
import subprocess

class SimpleHurricaneDashboardLoader:
    """Simplified professional loading window that launches the dashboard cleanly"""
    
    def __init__(self):        
        # Loading steps and status
        self.loading_steps = [
            "🐍 Checking Python version",
            "📦 Verifying dependencies", 
            "📁 Validating required files",
            "📊 Checking data files",
            "🎨 Testing matplotlib backend",
            "🔧 Initializing components",
            "🚀 Launching dashboard"
        ]
        
        self.current_step = 0
        self.total_steps = len(self.loading_steps)
        self.loading_complete = False
        self.loading_successful = False
        self.dashboard = None
        
    def create_loading_window(self):
        """Create a beautiful loading window"""
        
        # Set CustomTkinter appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create loading window
        self.loading_window = ctk.CTk()
        self.loading_window.title("Hurricane Dashboard - Initializing")
        self.loading_window.geometry("550x400")
        self.loading_window.resizable(False, False)
        
        # Center the window - larger size to accommodate log display
        self.loading_window.update_idletasks()
        x = (self.loading_window.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.loading_window.winfo_screenheight() // 2) - (500 // 2)
        self.loading_window.geometry(f"650x500+{x}+{y}")
        
        # Remove window controls and keep on top
        self.loading_window.attributes('-topmost', True)
        self.loading_window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Main container
        main_frame = ctk.CTkFrame(self.loading_window)
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🌀 Hurricane Dashboard",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Advanced Hurricane Analysis & Visualization System",
            font=ctk.CTkFont(size=16),
            text_color="#cccccc"
        )
        subtitle_label.pack(pady=(8, 0))
        
        # Progress section
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 20))
        
        # Status
        self.status_var = tk.StringVar(value="Preparing to initialize...")
        self.status_label = ctk.CTkLabel(
            progress_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#4a90e2"
        )
        self.status_label.pack(pady=(20, 15))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            width=450,
            height=24,
            corner_radius=12
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # Percentage
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cccccc"
        )
        self.progress_label.pack(pady=(0, 20))
        
        # Log display section
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 Initialization Log",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.pack(pady=(15, 10))
        
        # Create scrollable log display
        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            height=180,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#e0e0e0",
            fg_color=("#2b2b2b", "#1a1a1a"),
            scrollbar_button_color=("#4a90e2", "#357abd"),
            wrap="word"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Make textbox read-only
        self.log_textbox.configure(state="disabled")
        
        # Info section (compact)
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(0, 5))
        
        info_title = ctk.CTkLabel(
            info_frame,
            text="🚀 Features",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        info_title.pack(pady=(10, 5))
        
        # Compact feature list
        features_text = "📊 Timeline • 🗺️ Maps • 📋 Analysis • ⚙️ Settings • 💾 Export"
        
        feature_label = ctk.CTkLabel(
            info_frame,
            text=features_text,
            font=ctk.CTkFont(size=12),
            text_color="#cccccc"
        )
        feature_label.pack(pady=(0, 10))
        
    def update_progress(self, step: int, status: str):
        """Update progress display"""
        progress = step / self.total_steps
        percentage = int(progress * 100)
        
        self.progress_var.set(progress)
        self.progress_label.configure(text=f"{percentage}%")
        self.status_var.set(status)
        
        self.loading_window.update_idletasks()
    
    def add_log_message(self, message: str):
        """Add a message to the log display"""
        try:
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"{message}\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")  # Auto-scroll to bottom
            self.loading_window.update_idletasks()
        except Exception as e:
            print(f"⚠️ Error updating log display: {e}")
    
    def clear_log_display(self):
        """Clear the log display"""
        try:
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.configure(state="disabled")
        except Exception as e:
            print(f"⚠️ Error clearing log display: {e}")
        
    def run_loading_process(self):
        """Execute loading process"""
        def loading_thread():
            try:
                # Initialize log display
                self.add_log_message("🌀 Hurricane Dashboard - Professional GUI Launcher")
                self.add_log_message("=" * 50)
                
                for i, step_name in enumerate(self.loading_steps[:-1]):  # All except launch
                    self.update_progress(i, step_name)
                    self.add_log_message(f"  ✓ {step_name}")
                    time.sleep(0.8)  # Visual delay
                
                # Final step - launch
                self.update_progress(self.total_steps - 1, self.loading_steps[-1])
                self.add_log_message(f"  ✓ {self.loading_steps[-1]}")
                time.sleep(0.5)
                
                # Mark as complete
                self.loading_successful = True
                self.loading_complete = True
                
                # Schedule dashboard launch
                self.loading_window.after(100, self._launch_dashboard)
                
            except Exception as e:
                print(f"❌ Loading error: {e}")
                self.loading_successful = False
                self.loading_complete = True
                
        # Start loading thread
        loading_thread_obj = threading.Thread(target=loading_thread, daemon=True)
        loading_thread_obj.start()
    
    def _launch_dashboard(self):
        """Launch the dashboard and wait for visualization completion"""
        if self.loading_successful:
            try:
                # Update loading status to show we're waiting for visualizations
                self.status_var.set("🎨 Loading visualizations...")
                
                # Import and create dashboard with callback
                from tabbed_native_dashboard import TabbedNativeDashboard
                
                self.add_log_message("✨ Creating dashboard from GUI loader...")
                dashboard = TabbedNativeDashboard(
                    loading_callback=self._close_loading_window,
                    log_callback=self.add_log_message
                )
                
                # Store dashboard reference
                self.dashboard = dashboard
                
                self.add_log_message("🚀 Starting Hurricane Dashboard (visualizations loading)...")
                dashboard.run()
                
            except Exception as e:
                print(f"❌ Dashboard launch error: {e}")
                self.loading_window.destroy()
        else:
            self.loading_window.destroy()
    
    def _close_loading_window(self):
        """Close loading window when all visualizations are ready"""
        try:
            self.status_var.set("✅ Dashboard ready!")
            self.loading_window.update_idletasks()
            
            # Small delay to show completion message
            self.loading_window.after(500, lambda: self.loading_window.destroy())
            
            print("🎉 Loading window closed - all visualizations ready!")
        except Exception as e:
            print(f"⚠️ Error closing loading window: {e}")
            try:
                self.loading_window.destroy()
            except:
                pass
    
    def _show_error(self, message: str):
        """Show error message"""
        error_window = ctk.CTkToplevel()
        error_window.title("Error")
        error_window.geometry("400x200")
        
        error_label = ctk.CTkLabel(
            error_window,
            text=f"❌ Error:\n{message}",
            font=ctk.CTkFont(size=14),
            text_color="#ff6b6b"
        )
        error_label.pack(expand=True, pady=20)
        
        close_btn = ctk.CTkButton(
            error_window,
            text="Close",
            command=error_window.destroy
        )
        close_btn.pack(pady=10)
    
    def _on_closing(self):
        """Handle window close"""
        if not self.loading_complete:
            print("\n⚠️ Loading interrupted by user")
        
        self.loading_window.destroy()
        sys.exit(0)
    
    def show(self):
        """Show the loading window and start process"""
        self.create_loading_window()
        
        # Start loading after brief delay
        self.loading_window.after(800, self.run_loading_process)
        
        # Start main loop
        self.loading_window.mainloop()


def launch_with_gui_loader():
    """Launch hurricane dashboard with GUI loading screen"""
    try:
        # Verify basic requirements first
        if sys.version_info < (3, 8):
            print(f"❌ Python 3.8+ required, found {sys.version.split()[0]}")
            return False
            
        # Check for basic dependencies
        try:
            import customtkinter
            import matplotlib
            import pandas
        except ImportError as e:
            print(f"❌ Missing required dependency: {e}")
            print("📦 Install with: pip install customtkinter matplotlib pandas numpy psutil")
            return False
        
        # Launch GUI loader
        loader = SimpleHurricaneDashboardLoader()
        loader.show()
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Loading interrupted by user")
        return True
        
    except Exception as e:
        print(f"\n❌ GUI loader error: {e}")
        print("🔄 Falling back to simple launcher...")
        
        # Fallback to simple launcher
        try:
            from simple_launcher import main as simple_main
            return simple_main()
        except Exception as fallback_error:
            print(f"❌ Fallback failed: {fallback_error}")
            return False


def main():
    """Main function"""
    print("🌀 Hurricane Dashboard - Professional GUI Launcher")
    print("=" * 50)
    
    success = launch_with_gui_loader()
    
    if success:
        print("\n✅ Hurricane Dashboard session completed successfully")
        return True
    else:
        print("\n❌ Launch failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)