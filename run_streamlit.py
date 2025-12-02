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
    
    # Check if streamlit is available
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
        print("✅ Streamlit installed successfully!")
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    streamlit_app_path = script_dir / "streamlit_app.py"
    
    if not streamlit_app_path.exists():
        print(f"❌ Streamlit app not found at: {streamlit_app_path}")
        sys.exit(1)
    
    print(f"📄 App location: {streamlit_app_path}")
    print("🌐 Starting web interface...")
    print("   - The app will open in your browser automatically")
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
        sys.exit(1)

if __name__ == "__main__":
    main()