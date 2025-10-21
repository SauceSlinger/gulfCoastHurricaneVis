# Installation and Development Guide

## 🚀 Quick Start Installation

### For End Users (Simple Installation)

1. **Download the Repository**
   ```bash
   git clone https://github.com/SauceSlinger/gulfCoastHurricaneVis.git
   cd gulfCoastHurricaneVis
   ```

2. **One-Command Setup**
   ```bash
   python launch_tabbed.py
   ```
   
   The launcher will automatically:
   - Create a virtual environment
   - Install all required dependencies
   - Setup the database (if needed)
   - Launch the application

### For Advanced Users (Manual Setup)

1. **Create Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch Application**
   ```bash
   python launch_tabbed.py
   ```

## 🛠️ Development Setup

### Prerequisites for Development
- **Python 3.12+**
- **Git** for version control
- **PostgreSQL 12+** (optional, for database features)
- **Linux/Ubuntu/Mint** (recommended, tested platform)

### Development Installation

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gulfCoastHurricaneVis.git
   cd gulfCoastHurricaneVis
   ```

2. **Development Environment**
   ```bash
   # Create development virtual environment
   python3 -m venv .venv-dev
   source .venv-dev/bin/activate
   
   # Install development dependencies
   pip install -r requirements.txt
   pip install pytest flake8 black isort  # Development tools
   ```

3. **Run in Development Mode**
   ```bash
   # Run with debug logging
   HURRICANE_LOG_LEVEL=DEBUG python launch_tabbed.py
   
   # Run tests
   python -m pytest tests/
   
   # Run code formatting
   black . --line-length 120
   isort . --profile black
   flake8 . --max-line-length 120
   ```

## 📦 Package Dependencies

### Core Dependencies
```bash
# GUI Framework
customtkinter>=5.2.0        # Modern dark-themed GUI

# Data Processing  
pandas>=2.0.0               # Data manipulation
numpy>=1.24.0               # Numerical processing

# Visualization
matplotlib>=3.7.0           # Native plotting engine
plotly>=5.15.0             # Interactive visualizations (legacy)
seaborn>=0.12.0            # Statistical plotting

# Database (Optional)
psycopg2-binary>=2.9.0     # PostgreSQL connectivity
python-dotenv>=1.0.0       # Environment configuration

# Geographic Processing
geopandas>=0.13.0          # Geographic data handling
folium>=0.15.0             # Interactive mapping
shapely>=2.0.0             # Geometric operations

# System Monitoring
psutil>=5.9.0              # Performance monitoring

# Image Processing
pillow>=10.0.0             # Image manipulation support
```

### Development Dependencies
```bash
# Testing
pytest>=7.0.0             # Test framework
pytest-timeout>=2.1.0     # Test timeout handling

# Code Quality
flake8>=6.0.0              # Linting
black>=23.0.0              # Code formatting
isort>=5.12.0              # Import sorting

# Documentation
sphinx>=6.0.0             # Documentation generation
sphinx-rtd-theme>=1.2.0   # ReadTheDocs theme
```

## 🔧 Configuration Options

### Environment Variables
Create a `.env` file in the project root:
```bash
# Database Configuration (Optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hurricane_data
DB_USER=your_username
DB_PASSWORD=your_password

# Logging Configuration
HURRICANE_LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR

# Performance Tuning
CACHE_SIZE_LIMIT=100        # Maximum cached queries
BACKGROUND_THREADS=2        # Parallel processing threads
```

### Application Settings
Settings are automatically saved in `~/.hurricane_dashboard_settings.json`:
```json
{
  "overview": {
    "color_scheme": "dark",
    "show_statistics": true
  },
  "timeline": {
    "chart_type": "line",
    "show_trend": true
  },
  "map": {
    "show_coastline": true,
    "track_colors": "intensity"
  },
  "analysis": {
    "include_categories": [1, 2, 3, 4, 5],
    "statistical_tests": true
  }
}
```

## 🧪 Testing and Validation

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_performance.py -v
python -m pytest tests/test_visualizations.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Performance Testing
```bash
# Run performance benchmarks
python tests/test_performance.py

# Expected output:
✅ Database connected: 5,192 storms in 0.045s
✅ Sample query: 2,434 records in 0.127s
⚡ ViewManager initialized
🚀 Visualization generation: <2.0s
💾 Memory usage: <400 MB
```

### Manual Testing Checklist
- [ ] Application starts without errors
- [ ] All tabs load successfully
- [ ] Filters apply correctly
- [ ] Settings save and restore
- [ ] Map visualization displays regional data
- [ ] Export functions work
- [ ] Performance is acceptable (<2s for most operations)

## 🚀 Building and Distribution

### Creating a Release
```bash
# Tag the release
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin v2.0.0

# Create distribution packages
python setup.py sdist bdist_wheel

# Upload to PyPI (maintainers only)
python -m twine upload dist/*
```

### Creating Standalone Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile --windowed --name=hurricane-dashboard launch_tabbed.py

# Output will be in dist/hurricane-dashboard
```

## 🐛 Troubleshooting Development Issues

### Common Development Problems

1. **Import Errors**
   ```bash
   # Ensure virtual environment is activated
   source .venv/bin/activate
   
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test connection manually
   python -c "from database_manager import DatabaseManager; print(DatabaseManager().test_connection())"
   ```

3. **GUI Display Issues**
   ```bash
   # Check display environment
   echo $DISPLAY
   
   # Test matplotlib backend
   python -c "import matplotlib; print(matplotlib.get_backend())"
   
   # Install GUI libraries if missing
   sudo apt-get install python3-tk
   ```

4. **Memory Issues During Development**
   ```bash
   # Monitor memory usage
   python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available/1024**3:.1f} GB')"
   
   # Clear Python cache
   find . -type d -name "__pycache__" -exec rm -r {} +
   ```

### Debug Mode
```bash
# Run with verbose debugging
HURRICANE_LOG_LEVEL=DEBUG python launch_tabbed.py 2>&1 | tee debug.log

# Check specific component
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from native_visualizations import EnhancedNativeVisualizations
viz = EnhancedNativeVisualizations()
print('Visualization engine loaded successfully')
"
```

## 📁 Project Structure for Development

```
gulfCoastHurricaneVis/
├── 🚀 Application Entry Points
│   ├── launch_tabbed.py              # Main launcher
│   └── setup.py                      # Package setup
│
├── 🖥️ Core Application Files  
│   ├── tabbed_native_dashboard.py    # Main GUI application
│   ├── native_visualizations.py     # Visualization engine
│   ├── settings_manager.py          # Configuration management
│   └── logger_config.py             # Logging configuration
│
├── 📊 Data Processing
│   ├── data_processor_db.py         # Database data processing
│   ├── database_manager.py          # DB connection management
│   └── view_manager.py              # View coordination (legacy)
│
├── 📄 Data Files
│   ├── storms.csv                   # Hurricane dataset
│   └── database/                    # Database files
│
├── 🧪 Testing and Development
│   ├── tests/                       # Test suite
│   ├── deprecated/                  # Legacy code
│   └── docs/                       # Documentation
│
├── 📋 Project Metadata
│   ├── README.md                    # Main documentation
│   ├── requirements.txt             # Dependencies
│   ├── LICENSE                      # MIT license
│   ├── CHANGELOG.md                 # Version history
│   ├── .gitignore                   # Git ignore rules
│   └── .env.example                 # Environment template
└── 
```

## 🔄 Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/new-feature
   # Develop feature
   python -m pytest tests/
   git commit -am "Add new feature"
   git push origin feature/new-feature
   # Create pull request
   ```

2. **Code Review Checklist**
   - [ ] All tests pass
   - [ ] Code follows style guidelines (black, isort, flake8)
   - [ ] Documentation updated
   - [ ] Performance impact assessed
   - [ ] No debug prints or temporary code

3. **Release Process**
   - Update version in `setup.py`
   - Update `CHANGELOG.md`
   - Tag release
   - Update documentation
   - Test installation process

---

**Questions or Issues?**
- 📝 [Create an Issue](https://github.com/SauceSlinger/gulfCoastHurricaneVis/issues)
- 💬 [Join Discussions](https://github.com/SauceSlinger/gulfCoastHurricaneVis/discussions)
- 📧 Contact the maintainers

**Happy Coding! 🌀**