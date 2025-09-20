#!/usr/bin/env python3
"""
Test script for the web application
"""

import requests
import time
import sys

def test_web_app():
    """Test the API endpoints"""
    base_url = "http://localhost:7777"
    
    print("🧪 Testing Multi-Book RAG API")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("1. Testing API connection...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API is running: {data['name']} v{data['version']}")
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API not responding: {e}")
        print("   💡 Make sure to start the server with: python app.py")
        return False
    
    # Test 2: Check API status
    print("2. Testing API status...")
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"   ✅ System ready: {data['books_loaded']} books, {data['total_chunks']} chunks")
                print(f"   📚 Available books: {', '.join(data['available_books'])}")
            else:
                print(f"   ❌ API error: {data['error']}")
                return False
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API request failed: {e}")
        return False
    
    # Test 3: Check books endpoint
    print("3. Testing books endpoint...")
    try:
        response = requests.get(f"{base_url}/books", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                books = data['books']
                print(f"   ✅ Found {len(books)} books:")
                for book in books:
                    print(f"      - {book['book_title']} ({book['chunk_count']} chunks)")
            else:
                print(f"   ❌ Books API error: {data['error']}")
                return False
        else:
            print(f"   ❌ Books API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Books API request failed: {e}")
        return False
    
    # Test 4: Test a simple query
    print("4. Testing query endpoint...")
    try:
        query_data = {
            "question": "What is this story about?",
            "context_chunks": 20,
            "use_book_knowledge": True
        }
        
        response = requests.post(
            f"{base_url}/query", 
            json=query_data, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"   ✅ Query successful:")
                print(f"      - Processing time: {data['processing_time']}s")
                print(f"      - Context length: {data['context_length']:,} chars")
                print(f"      - Books searched: {len(data['books_searched'])}")
                print(f"      - Answer length: {len(data['answer'])} chars")
            else:
                print(f"   ❌ Query failed: {data['error']}")
                return False
        else:
            print(f"   ❌ Query API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Query request failed: {e}")
        return False
    
    print("\n🎉 All tests passed! API is working correctly.")
    print(f"🌐 API is running at: {base_url}")
    return True

if __name__ == "__main__":
    success = test_web_app()
    sys.exit(0 if success else 1)
