#!/usr/bin/env python3
"""
Test script for comprehensive entity extraction during book analysis
This will extract ALL characters, places, objects, and events during preprocessing
"""

import os
import json
from dotenv import load_dotenv

def test_comprehensive_extraction():
    """Test comprehensive entity extraction during book analysis"""
    print("🔍 Testing Comprehensive Entity Extraction")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set!")
        print("Please set your OpenRouter API key in the .env file")
        return
    
    try:
        from multi_book_analyzer import MultiBookAnalyzer
        
        # Initialize analyzer
        print("🔧 Initializing analyzer...")
        analyzer = MultiBookAnalyzer()
        
        # Get available books
        books = analyzer.get_available_books()
        print(f"📚 Available books: {len(books)}")
        
        if not books:
            print("❌ No books found!")
            return
        
        # Test comprehensive extraction on first book
        test_book = books[0]
        book_id = test_book['book_id']
        book_title = test_book['book_title']
        
        print(f"\n🔍 Testing comprehensive entity extraction for: {book_title}")
        print(f"   Book ID: {book_id}")
        
        # Analyze the book with comprehensive entity extraction
        print(f"\n📖 Starting comprehensive analysis...")
        print("   - Extracting ALL entities and relationships first")
        print("   - Using 400 chunks with 20,000 character context")
        print("   - Targeting 50-100+ entities and 100-200+ relationships")
        
        analysis = analyzer.analyze_single_book(book_id, force_refresh=True)
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return
        
        # Check knowledge graph results
        if 'knowledge_graph' in analysis:
            kg_data = analysis['knowledge_graph']
            
            if 'error' in kg_data:
                print(f"❌ Knowledge graph extraction failed: {kg_data['error']}")
                return
            
            entities = kg_data.get('entities', {})
            relationships = kg_data.get('relationships', [])
            
            print(f"\n✅ Comprehensive extraction results:")
            print(f"   📊 Entities: {len(entities)} (target: 50-100+)")
            print(f"   🔗 Relationships: {len(relationships)} (target: 100-200+)")
            
            # Show entity breakdown by type
            entity_types = {}
            for entity in entities.values():
                entity_type = entity.get('type', 'unknown')
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            print(f"\n📋 Entity breakdown by type:")
            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {entity_type}: {count}")
            
            # Show sample entities with details
            print(f"\n📋 Sample entities with details:")
            for i, (entity_id, entity) in enumerate(list(entities.items())[:10]):
                importance = entity.get('importance', 0.5)
                mentions = entity.get('mentions', [])
                print(f"   {i+1}. {entity['name']} ({entity['type']})")
                print(f"      Importance: {importance:.1f}")
                print(f"      Description: {entity.get('description', 'N/A')[:100]}...")
                if mentions:
                    print(f"      Mentions: {len(mentions)} quotes")
            
            # Show relationship types
            rel_types = {}
            for rel in relationships:
                rel_type = rel.get('type', 'unknown')
                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
            
            print(f"\n🔗 Relationship types (top 10):")
            for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   - {rel_type}: {count}")
            
            # Show sample relationships with evidence
            print(f"\n🔗 Sample relationships with evidence:")
            for i, rel in enumerate(relationships[:5]):
                from_name = entities[rel['from']]['name']
                to_name = entities[rel['to']]['name']
                strength = rel.get('strength', 0.5)
                evidence = rel.get('evidence', 'No evidence provided')
                print(f"   {i+1}. {from_name} --[{rel['type']}]--> {to_name}")
                print(f"      Strength: {strength:.1f}")
                print(f"      Evidence: {evidence[:100]}...")
            
            # Test force graph data generation
            print(f"\n🎯 Testing force graph data generation...")
            force_graph_data = analyzer.get_force_graph_data(book_id)
            
            if force_graph_data:
                nodes = force_graph_data.get('nodes', [])
                links = force_graph_data.get('links', [])
                
                print(f"✅ Force graph data generated!")
                print(f"   📊 Nodes: {len(nodes)}")
                print(f"   🔗 Links: {len(links)}")
                
                # Show node importance distribution
                importance_dist = {}
                for node in nodes:
                    importance = node.get('importance', 0.5)
                    importance_range = f"{int(importance * 10) * 0.1:.1f}-{int(importance * 10) * 0.1 + 0.1:.1f}"
                    importance_dist[importance_range] = importance_dist.get(importance_range, 0) + 1
                
                print(f"\n📊 Node importance distribution:")
                for range_str, count in sorted(importance_dist.items()):
                    print(f"   - {range_str}: {count} nodes")
            
            print(f"\n🎉 Comprehensive entity extraction complete!")
            print(f"💡 The force graph will now show much more comprehensive data")
            print(f"🌐 Visit http://localhost:7777/force-graph to see the improved visualization")
            
        else:
            print(f"❌ No knowledge graph found in analysis results")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🧪 Comprehensive Entity Extraction Test")
    print("=" * 60)
    
    # Test comprehensive extraction
    test_comprehensive_extraction()
    
    print(f"\n🏁 Test completed!")
    print(f"\n💡 Key improvements:")
    print(f"   1. Entity extraction happens during book analysis (preprocessing)")
    print(f"   2. Uses 20,000 character context (vs 8,000 before)")
    print(f"   3. Targets 50-100+ entities (vs 10 before)")
    print(f"   4. Targets 100-200+ relationships (vs 8 before)")
    print(f"   5. Includes evidence quotes and mention tracking")
    print(f"   6. All analysis methods now use comprehensive entity data")

if __name__ == "__main__":
    main()
