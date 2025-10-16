#!/usr/bin/env python3
"""
Simple startup script for the web application
"""

import os
import sys
import subprocess
import time

def start_web_app():
    """Start the web application"""
    print("🚀 Starting Multi-Book RAG Web Application...")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("💡 Please copy .env.example to .env and fill in your API keys:")
        print("   cp .env.example .env")
        print("   nano .env")
        return False
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Virtual environment not activated!")
        print("💡 Please activate the virtual environment:")
        print("   source venv/bin/activate")
        return False
    
    print("✅ Environment checks passed")
    print("🌐 Starting web server on all interfaces (0.0.0.0:7777)")
    print("📚 The system will check and analyze books that need analysis...")
    print("⏳ This may take a few moments if books need analysis...")
    print("💡 Books with valid cache will load instantly!")
    print()
    print("🎯 Once started, access the app at:")
    print("   http://localhost:7777 (local access)")
    print("   http://[your-ip]:7777 (network access)")
    print()
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the Flask app
        from app import app
        app.run(debug=False, host='0.0.0.0', port=7777)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = start_web_app()
    sys.exit(0 if success else 1)
