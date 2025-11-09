#!/usr/bin/env python3
"""
Simple startup script for the Keep in Touch chat application
Run this with: python run.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 3000))
    
    print("Starting Keep in Touch Chat Application")
    print(f"Server will be available at: http://localhost:{port}")
    print("Multi-chat powered by Google Gemini API")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)