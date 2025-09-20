#!/usr/bin/env python3
"""
Setup script to configure environment variables from .env file
"""

import os
from dotenv import load_dotenv

def setup_openrouter_env():
    """Set up environment variables from .env file"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("🔧 Loading environment variables from .env file...")
    
    # List of expected environment variables
    expected_vars = [
        'OPENROUTER_API_KEY',
        'OPENROUTER_MODEL', 
        'OPENROUTER_MAX_TOKENS',
        'OPENROUTER_TEMPERATURE',
        'OPENROUTER_FORCE_JSON',
        'QUESTION_FINAL_GRACE_MS',
        'TOKENIZERS_PARALLELISM',
        'CHROMADB_API_KEY',
        'CHROMADB_TENANT',
        'CHROMADB_DATABASE'
    ]
    
    # Display loaded variables (mask sensitive ones)
    for var in expected_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var or 'KEY' in var:
                # Mask API keys for security
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"   {var} = {display_value}")
        else:
            print(f"   {var} = ❌ NOT SET")
    
    print("\n✅ Environment configuration complete!")
    print("\n💡 You can now run:")
    print("   python main_multi_book.py")

if __name__ == "__main__":
    setup_openrouter_env()
