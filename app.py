#!/usr/bin/env python3
"""
Nomit WebApp - Main entry point for Render
"""

import os
import sys

# Add nomit_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nomit_app'))

# Import and run the server
from simple_server import start_server

if __name__ == "__main__":
    start_server()
