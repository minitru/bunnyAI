#!/usr/bin/env python3
"""
Test script for the caching functionality
"""

import os
import time
from setup_openrouter import setup_openrouter_env
from enhanced_rag import EnhancedRAG
from book_analyzer import BookAnalyzer

def test_caching_system():
    """Test the caching system"""
    print("🧪 Testing Caching System")
    print("="*60)
    
    # Setup environment
    setup_openrouter_env()
    
    # Test 1: First run (should create cache)
    print("📝 Test 1: First run (creating cache)")
    print("-" * 40)
    
    start_time = time.time()
    rag1 = EnhancedRAG()
    rag1.initialize_book_knowledge()
    
    # Test a query
    result1 = rag1.query("who won, blanche or elle", n_results=15, use_book_knowledge=True)
    first_run_time = time.time() - start_time
    
    print(f"⏱️ First run time: {first_run_time:.2f} seconds")
    print(f"💡 Answer: {result1['answer'][:100]}...")
    
    # Show cache info
    cache_info = rag1.get_cache_info()
    print(f"📊 Cache status: {cache_info.get('status')}")
    if cache_info.get('status') == 'valid':
        print(f"📅 Cache age: {cache_info.get('age_days', 0)} days, {cache_info.get('age_hours', 0)} hours")
    
    print("\n" + "="*60)
    
    # Test 2: Second run (should load from cache)
    print("📂 Test 2: Second run (loading from cache)")
    print("-" * 40)
    
    start_time = time.time()
    rag2 = EnhancedRAG()
    rag2.initialize_book_knowledge()
    
    # Test the same query
    result2 = rag2.query("who won, blanche or elle", n_results=15, use_book_knowledge=True)
    second_run_time = time.time() - start_time
    
    print(f"⏱️ Second run time: {second_run_time:.2f} seconds")
    print(f"💡 Answer: {result2['answer'][:100]}...")
    
    # Compare times
    speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
    print(f"🚀 Speedup: {speedup:.1f}x faster")
    
    print("\n" + "="*60)
    
    # Test 3: Force refresh
    print("🔄 Test 3: Force refresh (ignoring cache)")
    print("-" * 40)
    
    start_time = time.time()
    rag3 = EnhancedRAG()
    rag3.initialize_book_knowledge(force_refresh=True)
    
    result3 = rag3.query("who won, blanche or elle", n_results=15, use_book_knowledge=True)
    refresh_run_time = time.time() - start_time
    
    print(f"⏱️ Refresh run time: {refresh_run_time:.2f} seconds")
    print(f"💡 Answer: {result3['answer'][:100]}...")
    
    print("\n" + "="*60)
    
    # Test 4: Cache management
    print("🗂️ Test 4: Cache management")
    print("-" * 40)
    
    # Show detailed cache info
    cache_info = rag3.get_cache_info()
    print("📊 Detailed cache info:")
    for key, value in cache_info.items():
        print(f"   {key}: {value}")
    
    # Test cache clearing
    print("\n🗑️ Clearing cache...")
    rag3.clear_cache()
    
    # Check cache status after clearing
    cache_info_after = rag3.get_cache_info()
    print(f"📊 Cache status after clearing: {cache_info_after.get('status')}")
    
    print("\n" + "="*60)
    print("✅ Caching system test complete!")

def test_cache_persistence():
    """Test that cache persists between different instances"""
    print("\n🔄 Testing Cache Persistence")
    print("="*60)
    
    setup_openrouter_env()
    
    # Create first instance and initialize
    print("📝 Creating first instance...")
    rag1 = EnhancedRAG()
    rag1.initialize_book_knowledge()
    
    # Get cache info
    cache_info1 = rag1.get_cache_info()
    print(f"📊 Cache created: {cache_info1.get('status')}")
    
    # Create second instance (should load from cache)
    print("📂 Creating second instance...")
    rag2 = EnhancedRAG()
    
    # Check cache info before initialization
    cache_info2 = rag2.get_cache_info()
    print(f"📊 Cache available: {cache_info2.get('status')}")
    
    # Initialize (should be fast)
    start_time = time.time()
    rag2.initialize_book_knowledge()
    load_time = time.time() - start_time
    
    print(f"⏱️ Cache load time: {load_time:.2f} seconds")
    print("✅ Cache persistence test complete!")

def main():
    """Main test function"""
    print("🚀 Caching System Test Suite")
    print("="*60)
    
    try:
        # Test basic caching
        test_caching_system()
        
        # Test cache persistence
        test_cache_persistence()
        
        print("\n🎉 All caching tests completed!")
        print("\n💡 Key Benefits:")
        print("   ✅ First run: Creates comprehensive analysis")
        print("   ✅ Subsequent runs: Load from cache (much faster)")
        print("   ✅ Cache validation: Checks content changes")
        print("   ✅ Cache expiry: Automatically expires after 7 days")
        print("   ✅ Force refresh: Option to ignore cache")
        print("   ✅ Cache management: Clear and inspect cache")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
