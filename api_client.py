#!/usr/bin/env python3
"""
Example API client for the Multi-Book Enhanced RAG API
"""

import requests
import json

class LiteraryAnalysisAPI:
    def __init__(self, base_url="http://localhost:7777"):
        self.base_url = base_url.rstrip('/')
    
    def get_status(self):
        """Get API status"""
        response = requests.get(f"{self.base_url}/status")
        return response.json()
    
    def get_books(self):
        """Get available books"""
        response = requests.get(f"{self.base_url}/books")
        return response.json()
    
    def query(self, question, book=None, context_chunks=80, use_book_knowledge=True):
        """
        Query the API for literary analysis
        
        Args:
            question (str): Your question about the books
            book (str, optional): Book ID to query (defaults to all books)
            context_chunks (int): Number of context chunks (default: 80)
            use_book_knowledge (bool): Use book knowledge (default: True)
        
        Returns:
            dict: API response with analysis
        """
        payload = {
            "question": question,
            "context_chunks": context_chunks,
            "use_book_knowledge": use_book_knowledge
        }
        
        if book:
            payload["book"] = book
        
        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        return response.json()

def main():
    """Example usage of the API client"""
    api = LiteraryAnalysisAPI()
    
    print("🔍 Literary Analysis API Client")
    print("=" * 40)
    
    # Check status
    print("1. Checking API status...")
    status = api.get_status()
    if status['success']:
        print(f"   ✅ API ready: {status['books_loaded']} books, {status['total_chunks']} chunks")
        print(f"   📚 Available books: {', '.join(status['available_books'])}")
    else:
        print(f"   ❌ API error: {status['error']}")
        return
    
    print()
    
    # Get books
    print("2. Getting available books...")
    books = api.get_books()
    if books['success']:
        for book in books['books']:
            print(f"   📖 {book['book_title']} ({book['chunk_count']} chunks)")
    else:
        print(f"   ❌ Error: {books['error']}")
    
    print()
    
    # Example queries
    print("3. Example queries...")
    
    # Query all books
    print("   Querying all books: 'Who are the main characters?'")
    result = api.query("Who are the main characters?")
    if result['success']:
        print(f"   ✅ Answer length: {len(result['answer'])} chars")
        print(f"   📚 Books searched: {', '.join(result['books_searched'])}")
        print(f"   ⏱️  Processing time: {result['processing_time']}s")
        print(f"   📝 Answer preview: {result['answer'][:200]}...")
    else:
        print(f"   ❌ Query failed: {result['error']}")
    
    print()
    
    # Query specific book
    print("   Querying specific book: 'What is the main conflict?'")
    result = api.query("What is the main conflict?", book="sidetrackkey")
    if result['success']:
        print(f"   ✅ Answer length: {len(result['answer'])} chars")
        print(f"   📚 Books searched: {', '.join(result['books_searched'])}")
        print(f"   ⏱️  Processing time: {result['processing_time']}s")
        print(f"   📝 Answer preview: {result['answer'][:200]}...")
    else:
        print(f"   ❌ Query failed: {result['error']}")

if __name__ == "__main__":
    main()
