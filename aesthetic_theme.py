"""
Aesthetic Theme System for Gulf Coast Hurricane Visualization Dashboard.

This module provides comprehensive theming and styling for all UI components,
ensuring a consistent and professional appearance throughout the application.
"""

import customtkinter as ctk
from typing import Dict, Tuple, Any, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

@dataclass
class ColorPalette:
    """Color palette for the hurricane dashboard theme."""
    
    # Primary Application Colors
    primary: str = "#1f538d"           # Deep blue for primary elements
    primary_hover: str = "#2a5f9e"     # Slightly lighter blue for hover states
    secondary: str = "#14375e"         # Darker blue for secondary elements
    accent: str = "#ffa726"            # Orange accent for highlights and warnings
    accent_hover: str = "#ffb74d"      # Lighter orange for hover states
    
    # Background Colors
    bg_primary: str = "#0d1117"        # Very dark background
    bg_secondary: str = "#161b22"      # Slightly lighter background
    bg_tertiary: str = "#21262d"       # Card/panel background
    bg_quaternary: str = "#30363d"     # Input field background
    
    # Text Colors
    text_primary: str = "#f0f6fc"      # Primary text (light)
    text_secondary: str = "#8b949e"    # Secondary text (gray)
    text_tertiary: str = "#6e7681"     # Tertiary text (darker gray)
    text_accent: str = "#58a6ff"       # Accent text (blue)
    
    # Border and Separator Colors
    border_primary: str = "#30363d"    # Primary borders
    border_secondary: str = "#21262d"  # Secondary borders
    separator: str = "#373e47"         # Separators and dividers
    
    # Status Colors
    success: str = "#238636"           # Success messages/indicators
    warning: str = "#d29922"           # Warning messages/indicators
    error: str = "#da3633"             # Error messages/indicators
    info: str = "#1f6feb"              # Info messages/indicators
    
    # Hurricane Category Colors (for data visualization)
    tropical_storm: str = "#74c0fc"    # Light blue for tropical storms
    category_1: str = "#69db7c"        # Green for Category 1
    category_2: str = "#ffd43b"        # Yellow for Category 2
    category_3: str = "#ff922b"        # Orange for Category 3
    category_4: str = "#ff6b6b"        # Red for Category 4
    category_5: str = "#da77f2"        # Purple for Category 5
    
    # Chart and Visualization Colors
    chart_bg: str = "#0d1117"          # Chart background
    chart_grid: str = "#21262d"        # Chart grid lines
    chart_text: str = "#f0f6fc"        # Chart text
    map_ocean_bg: str = "#1a2332"      # Map ocean background (darker blue for dark theme)
    chart_accent: str = "#58a6ff"      # Chart accent elements

@dataclass
class Typography:
    """Typography settings for the dashboard."""
    
    # Font Families - Linux compatible
    primary_family: str = "DejaVu Sans"   # Primary font family (Linux compatible)
    mono_family: str = "DejaVu Sans Mono" # Monospace font family (Linux compatible)
    
    # Font Sizes
    title_size: int = 24               # Main title font size
    header_size: int = 18              # Section header font size
    subheader_size: int = 16           # Subsection header font size
    body_size: int = 14                # Body text font size
    caption_size: int = 12             # Caption/small text font size
    button_size: int = 14              # Button text font size
    
    # Font Weights
    light_weight: str = "normal"       # Light font weight
    normal_weight: str = "normal"      # Normal font weight
    bold_weight: str = "bold"          # Bold font weight

@dataclass
class Spacing:
    """Spacing and sizing constants for the dashboard."""
    
    # Padding
    xs: int = 4                        # Extra small padding
    sm: int = 8                        # Small padding
    md: int = 16                       # Medium padding
    lg: int = 24                       # Large padding
    xl: int = 32                       # Extra large padding
    
    # Component Heights
    button_height: int = 36            # Standard button height
    input_height: int = 32             # Standard input field height
    header_height: int = 60            # Header/navbar height
    tab_height: int = 40               # Tab button height
    
    # Border Radius
    radius_sm: int = 4                 # Small border radius
    radius_md: int = 8                 # Medium border radius
    radius_lg: int = 12                # Large border radius
    
    # Border Widths
    border_thin: int = 1               # Thin border
    border_medium: int = 2             # Medium border
    border_thick: int = 3              # Thick border

class AestheticTheme:
    """Main theme class that manages all aesthetic aspects of the application."""
    
    def __init__(self, theme_name: str = "hurricane_dark"):
        """Initialize the aesthetic theme."""
        self.theme_name = theme_name
        self.colors = ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()
        
        # Configure CustomTkinter appearance
        self._configure_customtkinter()
        
        # Configure matplotlib styling
        self._configure_matplotlib()
    
    def _configure_customtkinter(self):
        """Configure CustomTkinter appearance mode and color theme."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Don't override internal theme configurations - just use our styling methods
    
    def _configure_matplotlib(self):
        """Configure matplotlib styling to match the application theme."""
        plt.style.use('dark_background')
        
        # Custom matplotlib parameters
        plt.rcParams.update({
            'figure.facecolor': self.colors.chart_bg,
            'axes.facecolor': self.colors.chart_bg,
            'axes.edgecolor': self.colors.border_primary,
            'axes.labelcolor': self.colors.text_primary,
            'axes.spines.left': True,
            'axes.spines.bottom': True,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'xtick.color': self.colors.text_secondary,
            'ytick.color': self.colors.text_secondary,
            'text.color': self.colors.text_primary,
            'font.family': [self.typography.primary_family],
            'font.size': self.typography.body_size,
            'grid.color': self.colors.chart_grid,
            'grid.alpha': 0.3,
            'lines.linewidth': 2,
            'figure.autolayout': True,
            'savefig.facecolor': self.colors.chart_bg,
            'savefig.edgecolor': 'none'
        })
    
    def get_hurricane_colormap(self) -> LinearSegmentedColormap:
        """Create a custom colormap for hurricane categories."""
        colors = [
            self.colors.tropical_storm,
            self.colors.category_1,
            self.colors.category_2,
            self.colors.category_3,
            self.colors.category_4,
            self.colors.category_5
        ]
        return LinearSegmentedColormap.from_list("hurricane", colors)
    
    def get_styled_button(self, parent, text: str, command=None, 
                         style: str = "primary", **kwargs) -> ctk.CTkButton:
        """Create a styled button with consistent theming."""
        
        style_configs = {
            "primary": {
                "fg_color": self.colors.primary,
                "hover_color": self.colors.primary_hover,
                "text_color": self.colors.text_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.button_size, 
                                   weight=self.typography.normal_weight)
            },
            "secondary": {
                "fg_color": self.colors.bg_quaternary,
                "hover_color": self.colors.border_primary,
                "text_color": self.colors.text_primary,
                "border_width": self.spacing.border_thin,
                "border_color": self.colors.border_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.button_size)
            },
            "accent": {
                "fg_color": self.colors.accent,
                "hover_color": self.colors.accent_hover,
                "text_color": self.colors.bg_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.button_size, 
                                   weight=self.typography.bold_weight)
            },
            "danger": {
                "fg_color": self.colors.error,
                "hover_color": "#e74c3c",
                "text_color": self.colors.text_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.button_size)
            }
        }
        
        config = style_configs.get(style, style_configs["primary"])
        config.update(kwargs)
        
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=self.spacing.button_height,
            corner_radius=self.spacing.radius_md,
            **config
        )
    
    def get_styled_frame(self, parent, style: str = "primary", **kwargs) -> ctk.CTkFrame:
        """Create a styled frame with consistent theming."""
        
        style_configs = {
            "primary": {
                "fg_color": self.colors.bg_tertiary,
                "border_color": self.colors.border_primary,
                "border_width": self.spacing.border_thin,
                "corner_radius": self.spacing.radius_md
            },
            "secondary": {
                "fg_color": self.colors.bg_secondary,
                "border_color": self.colors.border_secondary,
                "border_width": 0,
                "corner_radius": self.spacing.radius_md
            },
            "card": {
                "fg_color": self.colors.bg_tertiary,
                "border_color": self.colors.border_primary,
                "border_width": self.spacing.border_thin,
                "corner_radius": self.spacing.radius_lg
            },
            "transparent": {
                "fg_color": "transparent",
                "border_width": 0,
                "corner_radius": 0
            }
        }
        
        config = style_configs.get(style, style_configs["primary"])
        
        # Allow kwargs to override any config values
        for key, value in kwargs.items():
            config[key] = value
        
        return ctk.CTkFrame(parent, **config)
    
    def get_styled_label(self, parent, text: str, style: str = "body", **kwargs) -> ctk.CTkLabel:
        """Create a styled label with consistent theming."""
        
        style_configs = {
            "title": {
                "text_color": self.colors.text_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.title_size, 
                                   weight=self.typography.bold_weight)
            },
            "header": {
                "text_color": self.colors.text_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.header_size, 
                                   weight=self.typography.bold_weight)
            },
            "subheader": {
                "text_color": self.colors.text_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.subheader_size, 
                                   weight=self.typography.normal_weight)
            },
            "body": {
                "text_color": self.colors.text_primary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.body_size)
            },
            "caption": {
                "text_color": self.colors.text_secondary,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.caption_size)
            },
            "accent": {
                "text_color": self.colors.text_accent,
                "font": ctk.CTkFont(family=self.typography.primary_family, 
                                   size=self.typography.body_size, 
                                   weight=self.typography.bold_weight)
            }
        }
        
        config = style_configs.get(style, style_configs["body"])
        config.update(kwargs)
        
        return ctk.CTkLabel(parent, text=text, **config)
    
    def get_styled_entry(self, parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
        """Create a styled entry field with consistent theming."""
        
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=self.spacing.input_height,
            corner_radius=self.spacing.radius_sm,
            fg_color=self.colors.bg_quaternary,
            border_color=self.colors.border_primary,
            text_color=self.colors.text_primary,
            placeholder_text_color=self.colors.text_tertiary,
            font=ctk.CTkFont(family=self.typography.primary_family, 
                           size=self.typography.body_size),
            **kwargs
        )
    
    def get_styled_combobox(self, parent, values: list = None, **kwargs) -> ctk.CTkComboBox:
        """Create a styled combobox with consistent theming."""
        
        return ctk.CTkComboBox(
            parent,
            values=values or [],
            height=self.spacing.input_height,
            corner_radius=self.spacing.radius_sm,
            fg_color=self.colors.bg_quaternary,
            border_color=self.colors.border_primary,
            text_color=self.colors.text_primary,
            dropdown_fg_color=self.colors.bg_tertiary,
            dropdown_text_color=self.colors.text_primary,
            dropdown_hover_color=self.colors.primary,
            font=ctk.CTkFont(family=self.typography.primary_family, 
                           size=self.typography.body_size),
            **kwargs
        )
    
    def get_styled_checkbox(self, parent, text: str, **kwargs) -> ctk.CTkCheckBox:
        """Create a styled checkbox with consistent theming."""
        
        return ctk.CTkCheckBox(
            parent,
            text=text,
            fg_color=self.colors.primary,
            hover_color=self.colors.primary_hover,
            checkmark_color=self.colors.text_primary,
            text_color=self.colors.text_primary,
            font=ctk.CTkFont(family=self.typography.primary_family, 
                           size=self.typography.body_size),
            **kwargs
        )
    
    def get_chart_style_dict(self) -> Dict[str, Any]:
        """Get a dictionary of chart styling parameters."""
        return {
            'facecolor': self.colors.chart_bg,
            'edgecolor': self.colors.border_primary,
            'linewidth': 2,
            'alpha': 0.8,
            'grid': True,
            'grid_color': self.colors.chart_grid,
            'grid_alpha': 0.3,
            'text_color': self.colors.text_primary,
            'label_color': self.colors.text_secondary,
            'title_color': self.colors.text_primary,
            'title_size': self.typography.header_size,
            'label_size': self.typography.body_size,
            'tick_size': self.typography.caption_size
        }
    
    def apply_chart_styling(self, fig, ax):
        """Apply consistent styling to a matplotlib figure and axes."""
        # Set figure background
        fig.patch.set_facecolor(self.colors.chart_bg)
        
        # Set axes background and spines
        ax.set_facecolor(self.colors.chart_bg)
        for spine in ax.spines.values():
            spine.set_color(self.colors.border_primary)
            spine.set_linewidth(1)
        
        # Hide top and right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Style grid
        ax.grid(True, color=self.colors.chart_grid, alpha=0.3, linewidth=0.5)
        
        # Style ticks and labels
        ax.tick_params(colors=self.colors.text_secondary, labelsize=self.typography.caption_size)
        ax.xaxis.label.set_color(self.colors.text_primary)
        ax.yaxis.label.set_color(self.colors.text_primary)
        
        # Style title
        if ax.get_title():
            ax.title.set_color(self.colors.text_primary)
            ax.title.set_fontsize(self.typography.header_size)
            ax.title.set_fontweight(self.typography.bold_weight)

# Global theme instance
theme = AestheticTheme()

def get_theme() -> AestheticTheme:
    """Get the global theme instance."""
    return theme

def set_theme(new_theme: AestheticTheme):
    """Set a new global theme instance."""
    global theme
    theme = new_theme