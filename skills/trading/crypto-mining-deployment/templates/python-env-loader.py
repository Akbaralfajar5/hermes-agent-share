#!/usr/bin/env python3
"""
Python .env Auto-Loader Template

Problem: `source .env` in bash doesn't pass environment variables to Python subprocesses.

Solution: Load .env directly in Python at import time.

Usage:
    1. Copy this function to the top of your script
    2. Call load_env() before accessing os.getenv()
    3. Place .env file in same directory as script
"""

import os

def load_env():
    """
    Load environment variables from .env file in script directory.
    
    Supports:
    - KEY=value format
    - Comments (lines starting with #)
    - Empty lines
    - Quoted values (strips quotes)
    
    Does NOT support:
    - Variable expansion ($VAR, ${VAR})
    - Multi-line values
    - Export statements
    """
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_file):
        return  # Silently skip if .env doesn't exist
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=value
            if '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Strip quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # Set environment variable
            os.environ[key] = value

# Load .env at import time
load_env()

# Now you can use os.getenv() normally
if __name__ == "__main__":
    # Example usage
    api_key = os.getenv("API_KEY", "default_value")
    eth_address = os.getenv("ETH_ADDRESS", "")
    
    print(f"API_KEY: {api_key}")
    print(f"ETH_ADDRESS: {eth_address}")
