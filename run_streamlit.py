#!/usr/bin/env python3

"""
RFP Studio - Streamlit App Runner

Simple script to launch the Streamlit frontend for RFP Studio.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Streamlit application."""
    
    print("🚀 Starting RFP Studio - Streamlit Frontend")
    print("=" * 50)
    
    # Verify we're in the correct directory
    script_dir = Path(__file__).parent
    print(f"📁 Working directory: {script_dir}")
    
    # Check for required files
    required_files = ["streamlit_app.py", "document_processor.py", "requirements.txt"]
    missing_files = []
    
    for file in required_files:
        if not (script_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("Make sure you're running this from the RFP Studio root directory.")
        sys.exit(1)
    
    # Check if streamlit is available
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
            print("✅ Streamlit installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Streamlit: {e}")
            print("Please install manually: pip install streamlit")
            sys.exit(1)
    
    # Check for RFP Studio modules
    sys.path.insert(0, str(script_dir))
    try:
        import rfp_studio
        print("✅ RFP Studio modules found")
    except ImportError:
        print("⚠️  RFP Studio modules not found - some features may be limited")
        print("Make sure to set up your .env file with MongoDB and OpenAI credentials")
    
    # Get the streamlit app path
    streamlit_app_path = script_dir / "streamlit_app.py"
    
    print(f"📄 App location: {streamlit_app_path}")
    print("🌐 Starting web interface...")
    print("   - The app will open in your browser automatically")
    print("   - Access at: http://localhost:8501")
    print("   - Use Ctrl+C to stop the server")
    print("=" * 50)
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(streamlit_app_path),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\\n👋 Shutting down RFP Studio frontend...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        print("\\nTroubleshooting:")
        print("1. Make sure you're in the RFP Studio directory")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Set up your .env file with API keys")
        sys.exit(1)

if __name__ == "__main__":
    main()