#!/usr/bin/env python3
"""
Gear Metrology API Startup Script
Easy way to start the API server with proper configuration
"""

import subprocess
import sys
import os
import time
import webbrowser

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print(f"💡 Install with: pip install fastapi uvicorn pydantic")
        return False

def start_server():
    """Start the API server"""
    print("🚀 Starting Gear Metrology API Server...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check if MOP.py and gear_metrology_agent.py exist
    if not os.path.exists("MOP.py"):
        print("❌ MOP.py not found in current directory")
        return
    
    if not os.path.exists("gear_metrology_agent.py"):
        print("❌ gear_metrology_agent.py not found in current directory")
        return
    
    print("✅ Dependencies and files found")
    print("🌐 Starting server...")
    print()
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Alternative docs at: http://localhost:8000/redoc")
    print("🏠 Home page at: http://localhost:8000/")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Small delay then open browser
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open("http://localhost:8000/docs")
        except:
            pass
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the server
    try:
        import uvicorn
        uvicorn.run(
            "gear_api:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server()