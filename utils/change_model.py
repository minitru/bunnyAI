#!/usr/bin/env python3
"""
Quick Model Changer
"""

import os
from setup_openrouter import setup_openrouter_env

def change_model(new_model: str):
    """
    Change the model in the setup file
    
    Args:
        new_model: The new model ID to use
    """
    # Read current setup file
    with open('setup_openrouter.py', 'r') as f:
        content = f.read()
    
    # Find and replace the model line
    import re
    pattern = r"'OPENROUTER_MODEL': '[^']*'"
    replacement = f"'OPENROUTER_MODEL': '{new_model}'"
    
    new_content = re.sub(pattern, replacement, content)
    
    # Write back to file
    with open('setup_openrouter.py', 'w') as f:
        f.write(new_content)
    
    print(f"✅ Model changed to: {new_model}")

def main():
    """Interactive model changer"""
    print("🔄 Model Changer")
    print("="*40)
    
    models = {
        "1": "openai/gpt-4o-mini",
        "2": "openai/gpt-4o", 
        "3": "anthropic/claude-3.5-sonnet",
        "4": "google/gemini-pro-1.5",
        "5": "meta-llama/llama-3.1-405b-instruct"
    }
    
    print("Available models:")
    print("1. GPT-4o Mini (fast, cheap)")
    print("2. GPT-4o (best quality, expensive)")
    print("3. Claude 3.5 Sonnet (excellent analysis)")
    print("4. Gemini Pro 1.5 (long context)")
    print("5. Llama 3.1 405B (open source)")
    
    choice = input("\nSelect model (1-5): ").strip()
    
    if choice in models:
        change_model(models[choice])
        print(f"\n💡 To use the new model, restart your RAG system")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
