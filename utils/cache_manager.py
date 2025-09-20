#!/usr/bin/env python3
"""
Cache Management Utility for Book Analysis
"""

import os
import json
from datetime import datetime, timedelta
from setup_openrouter import setup_openrouter_env
from enhanced_rag import EnhancedRAG

def show_cache_status():
    """Show current cache status"""
    print("📊 Cache Status")
    print("="*40)
    
    setup_openrouter_env()
    rag = EnhancedRAG()
    
    cache_info = rag.get_cache_info()
    
    if cache_info.get('status') == 'no_cache':
        print("❌ No cache found")
        return
    
    print(f"📂 Status: {cache_info.get('status')}")
    print(f"📅 Created: {cache_info.get('created_at')}")
    print(f"⏰ Age: {cache_info.get('age_days', 0)} days, {cache_info.get('age_hours', 0)} hours")
    print(f"🤖 Model: {cache_info.get('model')}")
    print(f"📋 Components: {', '.join(cache_info.get('analysis_keys', []))}")
    print(f"🔑 Content Hash: {cache_info.get('content_hash', 'unknown')[:16]}...")

def clear_cache():
    """Clear the analysis cache"""
    print("🗑️ Clearing Cache")
    print("="*40)
    
    setup_openrouter_env()
    rag = EnhancedRAG()
    
    rag.clear_cache()
    print("✅ Cache cleared successfully")

def refresh_cache():
    """Force refresh the cache"""
    print("🔄 Refreshing Cache")
    print("="*40)
    
    setup_openrouter_env()
    rag = EnhancedRAG()
    
    print("This will re-analyze the entire book...")
    rag.initialize_book_knowledge(force_refresh=True)
    print("✅ Cache refreshed successfully")

def test_cache_speed():
    """Test cache loading speed"""
    print("⚡ Testing Cache Speed")
    print("="*40)
    
    setup_openrouter_env()
    rag = EnhancedRAG()
    
    import time
    
    # Test cache load
    start_time = time.time()
    rag.initialize_book_knowledge()
    load_time = time.time() - start_time
    
    print(f"⏱️ Cache load time: {load_time:.2f} seconds")
    
    # Test a quick query
    start_time = time.time()
    result = rag.query("who won, blanche or elle", n_results=10, use_book_knowledge=True)
    query_time = time.time() - start_time
    
    print(f"⏱️ Query time: {query_time:.2f} seconds")
    print(f"💡 Answer: {result['answer'][:100]}...")

def main():
    """Main cache management interface"""
    print("🗂️ Book Analysis Cache Manager")
    print("="*50)
    
    while True:
        print("\nOptions:")
        print("1. Show cache status")
        print("2. Clear cache")
        print("3. Refresh cache")
        print("4. Test cache speed")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            show_cache_status()
        elif choice == '2':
            clear_cache()
        elif choice == '3':
            refresh_cache()
        elif choice == '4':
            test_cache_speed()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
