#!/usr/bin/env python3
"""
Simple server starter for CropGuard AI
This script starts the Flask application without background processes.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from App import app

    print("🚀 Starting CropGuard AI Web Server...")
    print("🌐 Access at: http://localhost:8000")
    print("📊 Model loaded and ready for predictions")
    print("⚡ Threaded mode enabled for better performance")
    print("\nPress Ctrl+C to stop the server\n")

    # Start the server
    app.run(
        debug=False,
        host='0.0.0.0',
        port=8000,
        threaded=True,
        use_reloader=False
    )

except KeyboardInterrupt:
    print("\n👋 Server stopped by user")
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()