#!/usr/bin/env python3
"""
Test script for Knowledge Graph functionality
Tests the extraction and storage of knowledge graphs from books
"""

import os
import json
from dotenv import load_dotenv
from multi_book_analyzer import MultiBookAnalyzer

def test_knowledge_graph_extraction():
    """Test knowledge graph extraction on existing books"""
    print("🕸️ Testing Knowledge Graph Extraction")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set!")
        return
    
    try:
        # Initialize analyzer
        analyzer = MultiBookAnalyzer()
        
        # Get available books
        books = analyzer.get_available_books()
        print(f"📚 Available books: {len(books)}")
        for book in books:
            print(f"   - {book['book_title']} ({book['chunk_count']} chunks)")
        
        if not books:
            print("❌ No books found!")
            return
        
        # Test knowledge graph extraction on first book
        test_book = books[0]
        book_id = test_book['book_id']
        book_title = test_book['book_title']
        
        print(f"\n🔍 Testing knowledge graph extraction for: {book_title}")
        print(f"   Book ID: {book_id}")
        
        # Analyze the book (this will extract the knowledge graph)
        print(f"\n📖 Starting analysis...")
        analysis = analyzer.analyze_single_book(book_id, force_refresh=True)
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return
        
        # Check if knowledge graph was extracted
        if 'knowledge_graph' in analysis:
            kg_data = analysis['knowledge_graph']
            
            if 'error' in kg_data:
                print(f"❌ Knowledge graph extraction failed: {kg_data['error']}")
                return
            
            entities = kg_data.get('entities', {})
            relationships = kg_data.get('relationships', [])
            
            print(f"✅ Knowledge graph extracted successfully!")
            print(f"   📊 Entities: {len(entities)}")
            print(f"   🔗 Relationships: {len(relationships)}")
            
            # Display some entities
            print(f"\n📋 Sample Entities:")
            for i, (entity_id, entity_data) in enumerate(list(entities.items())[:5]):
                print(f"   {i+1}. {entity_data['name']} ({entity_data['type']})")
                print(f"      Description: {entity_data.get('description', 'N/A')[:100]}...")
            
            # Display some relationships
            print(f"\n🔗 Sample Relationships:")
            for i, rel in enumerate(relationships[:5]):
                from_entity = entities.get(rel['from'], {}).get('name', rel['from'])
                to_entity = entities.get(rel['to'], {}).get('name', rel['to'])
                print(f"   {i+1}. {from_entity} --[{rel['type']}]--> {to_entity}")
                print(f"      Strength: {rel.get('strength', 0.5)}")
            
            # Test force graph data generation
            print(f"\n🎯 Testing force graph data generation...")
            force_graph_data = analyzer.get_force_graph_data(book_id)
            
            if force_graph_data:
                nodes = force_graph_data.get('nodes', [])
                links = force_graph_data.get('links', [])
                metadata = force_graph_data.get('metadata', {})
                
                print(f"✅ Force graph data generated!")
                print(f"   📊 Nodes: {len(nodes)}")
                print(f"   🔗 Links: {len(links)}")
                print(f"   📚 Book: {metadata.get('book_id', 'N/A')}")
                
                # Test entity search
                print(f"\n🔍 Testing entity search...")
                search_results = analyzer.search_entities("character", book_id, limit=3)
                
                if search_results:
                    print(f"✅ Entity search working!")
                    print(f"   Found {len(search_results)} entities matching 'character':")
                    for entity in search_results:
                        print(f"   - {entity['name']} ({entity['type']})")
                else:
                    print(f"⚠️ No entities found for search 'character'")
            
            # Test combined force graph (if multiple books)
            if len(books) > 1:
                print(f"\n🌐 Testing combined force graph...")
                combined_data = analyzer.get_combined_force_graph_data()
                
                if combined_data:
                    combined_nodes = combined_data.get('nodes', [])
                    combined_links = combined_data.get('links', [])
                    combined_metadata = combined_data.get('metadata', {})
                    
                    print(f"✅ Combined force graph generated!")
                    print(f"   📊 Total Nodes: {len(combined_nodes)}")
                    print(f"   🔗 Total Links: {len(combined_links)}")
                    print(f"   📚 Books: {combined_metadata.get('books', [])}")
            
            print(f"\n🎉 Knowledge graph system is working correctly!")
            
        else:
            print(f"❌ No knowledge graph found in analysis results")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test the API endpoints for knowledge graph functionality"""
    print(f"\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    import requests
    
    base_url = "http://localhost:7777"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("❌ API server not responding correctly")
            return
    except requests.exceptions.RequestException:
        print("❌ API server not running. Start with: python app.py")
        return
    
    # Test books endpoint
    try:
        response = requests.get(f"{base_url}/api/books")
        if response.status_code == 200:
            books_data = response.json()
            if books_data.get('success'):
                books = books_data.get('books', [])
                print(f"✅ Books endpoint working - {len(books)} books available")
                
                if books:
                    # Test force graph endpoint
                    book_id = books[0]['book_id']
                    response = requests.get(f"{base_url}/api/force-graph/{book_id}")
                    if response.status_code == 200:
                        print(f"✅ Force graph endpoint working for {book_id}")
                    else:
                        print(f"⚠️ Force graph endpoint returned status {response.status_code}")
                    
                    # Test combined force graph endpoint
                    response = requests.get(f"{base_url}/api/force-graph/combined")
                    if response.status_code == 200:
                        print(f"✅ Combined force graph endpoint working")
                    else:
                        print(f"⚠️ Combined force graph endpoint returned status {response.status_code}")
                    
                    # Test entity search endpoint
                    search_data = {"query": "character", "book_id": book_id, "limit": 5}
                    response = requests.post(f"{base_url}/api/entities/search", json=search_data)
                    if response.status_code == 200:
                        print(f"✅ Entity search endpoint working")
                    else:
                        print(f"⚠️ Entity search endpoint returned status {response.status_code}")
            else:
                print(f"❌ Books endpoint returned error: {books_data.get('error')}")
        else:
            print(f"❌ Books endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")

def main():
    """Main test function"""
    print("🧪 Knowledge Graph System Test Suite")
    print("=" * 60)
    
    # Test knowledge graph extraction
    test_knowledge_graph_extraction()
    
    # Test API endpoints
    test_api_endpoints()
    
    print(f"\n🏁 Test suite completed!")
    print(f"\n💡 Next steps:")
    print(f"   1. Start the web server: python app.py")
    print(f"   2. Visit http://localhost:7777 to see the web interface")
    print(f"   3. Use the API endpoints to get force graph data")
    print(f"   4. Integrate with D3.js or similar for visualization")

if __name__ == "__main__":
    main()
