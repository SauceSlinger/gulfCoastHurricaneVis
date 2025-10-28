#!/usr/bin/env python3

"""
Hurricane Dashboard - Professional Launcher

Complete launcher with professional loading interface and fallback options.
Ensures database setup and optimal performance before launching the dashboard.
"""


import sysimport os

import osimport sys

from pathlib import Pathimport subprocess

import time

def main():from pathlib import Path

    """Main launcher with professional loading interface"""

    def check_requirements():

    # Add current directory to Python path    """Check if all required packages are installed"""

    current_dir = Path(__file__).parent    required_packages = [

    if str(current_dir) not in sys.path:        'customtkinter',

        sys.path.insert(0, str(current_dir))        'plotly',

            'pandas',

    print("🌀 Hurricane Dashboard - Professional Edition")        'numpy',

    print("🚀 Enhanced Tabbed Interface with Loading Screen")        'psycopg2-binary',

    print()        'python-dotenv'

        ]

    try:    

        # Launch with GUI loading screen    print("🔍 Checking required packages...")

        from gui_launcher import launch_with_gui_loader    missing_packages = []

        return launch_with_gui_loader()    

            for package in required_packages:

    except ImportError as e:        try:

        # Fallback to simple launcher if GUI fails            __import__(package.replace('-', '_'))

        print(f"⚠️ GUI loading unavailable: {e}")            print(f"  ✅ {package}")

        print("🔄 Using simplified launcher...")        except ImportError:

                    print(f"  ❌ {package} (missing)")

        try:            missing_packages.append(package)

            from simple_launcher import main as simple_main    

            return simple_main()    if missing_packages:

        except Exception as fallback_error:        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")

            print(f"❌ Simplified launcher failed: {fallback_error}")        try:

                        subprocess.check_call([

            # Final fallback to original launcher                sys.executable, '-m', 'pip', 'install'

            print("🔄 Using original launcher...")            ] + missing_packages)

            try:            print("✅ All packages installed successfully")

                from launch_tabbed import main as original_main        except subprocess.CalledProcessError as e:

                return original_main()            print(f"❌ Failed to install packages: {e}")

            except Exception as final_error:            return False

                print(f"❌ All launchers failed: {final_error}")    

                return False    return True

            

    except KeyboardInterrupt:def check_postgresql():

        print("\\n🛑 Launch interrupted by user")    """Check if PostgreSQL is installed and accessible"""

        return True    try:

                result = subprocess.run(['which', 'psql'], capture_output=True, text=True)

    except Exception as e:        if result.returncode != 0:

        print(f"\\n❌ Launch failed: {e}")            return False

        print("\\n💡 Troubleshooting tips:")        

        print("   1. Ensure all dependencies are installed:")        result = subprocess.run(['pg_isready'], capture_output=True, text=True)

        print("      pip install customtkinter matplotlib pandas numpy psutil")        return result.returncode == 0

        print("   2. Verify all Python files are present")    except:

        print("   3. Check system GUI support")        return False

        return False

def setup_database():

    """Set up the database if needed, with fallback to CSV"""

if __name__ == "__main__":    print("\n🗄️  Checking database options...")

    success = main()    

    if success:    # First check if PostgreSQL is available

        print("\\n✅ Hurricane Dashboard completed successfully")    if not check_postgresql():

        sys.exit(0)        print("⚠️  PostgreSQL not found or not running")

    else:        print("🔄 Falling back to CSV-based data processing")

        sys.exit(1)        print("💡 For better performance, install PostgreSQL: sudo apt install postgresql postgresql-contrib")
        return True  # Continue with CSV-based system
    
    try:
        # Check if we can import our database modules
        from database_manager import DatabaseManager
        
        # Test database connection
        db_manager = DatabaseManager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM storms")
            storm_count = cursor.fetchone()[0]
        
        if storm_count > 0:
            print(f"✅ Database ready: {storm_count:,} storms available")
            return True
        else:
            print("⚠️  Database empty, running migration...")
            return run_migration()
            
    except Exception as e:
        print(f"⚠️  Database not ready: {e}")
        print("� Falling back to CSV-based data processing")
        return True  # Continue with CSV fallback

def run_setup():
    """Run the database setup script"""
    try:
        result = subprocess.run([
            sys.executable, 'setup_database.py'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Database setup completed")
            return True
        else:
            print(f"❌ Database setup failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Database setup timed out")
        return False
    except Exception as e:
        print(f"❌ Error running database setup: {e}")
        return False

def run_migration():
    """Run the data migration script"""
    try:
        result = subprocess.run([
            sys.executable, 'migrate_data.py'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Data migration completed")
            return True
        else:
            print(f"❌ Data migration failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Data migration timed out")
        return False
    except Exception as e:
        print(f"❌ Error running data migration: {e}")
        return False

def run_performance_test():
    """Run quick performance test"""
    print("\n⚡ Running performance test...")
    
    try:
        result = subprocess.run([
            sys.executable, 'test_performance.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Performance test passed")
            # Show key performance metrics from the output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Database connected:' in line or 'Sample query:' in line or 'All tests passed!' in line:
                    print(f"  📊 {line.strip()}")
            return True
        else:
            print("⚠️  Performance test had issues:")
            print(result.stdout[-500:])  # Show last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Performance test timed out")
        return False
    except Exception as e:
        print(f"⚠️  Error running performance test: {e}")
        return False

def launch_dashboard():
    """Launch the main dashboard application"""
    print("\n🚀 Launching Hurricane Dashboard...")
    
    try:
        # Launch the dashboard
        os.execv(sys.executable, [sys.executable, 'dashboard.py'])
        
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")
        return False

def main():
    """Main launcher function"""
    print("🌀 Gulf Coast Hurricane Visualization Dashboard")
    print("=" * 55)
    print("Enhanced Performance Edition with PostgreSQL Backend")
    print("=" * 55)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please install missing packages manually.")
        sys.exit(1)
    
    # Step 2: Setup database
    if not setup_database():
        print("\n❌ Database setup failed. Please check your PostgreSQL installation.")
        print("💡 Make sure PostgreSQL is running and accessible.")
        sys.exit(1)
    
    # Step 3: Run performance test (optional, but recommended)
    performance_ok = run_performance_test()
    if not performance_ok:
        print("\n⚠️  Performance test indicated potential issues.")
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Setup cancelled.")
            sys.exit(1)
    
    # Step 4: Launch dashboard
    print("\n🎯 Everything looks good! Launching dashboard...")
    time.sleep(1)
    
    launch_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)