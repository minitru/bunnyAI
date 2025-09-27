#!/usr/bin/env python3
"""
Script to refresh knowledge graph with improved extraction
This will create a much more comprehensive knowledge graph
"""

import os
import json
import pickle
from datetime import datetime
from dotenv import load_dotenv

def refresh_knowledge_graph_manually():
    """Manually refresh the knowledge graph with improved extraction"""
    print("🔄 Refreshing Knowledge Graph with Improved Extraction")
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
        
        # Show current knowledge graph stats
        book_id = "wanda & me - act 1"
        current_kg = analyzer.get_knowledge_graph(book_id)
        
        if current_kg:
            current_entities = len(current_kg.get('entities', {}))
            current_relationships = len(current_kg.get('relationships', []))
            print(f"\n📊 Current knowledge graph for '{book_id}':")
            print(f"   Entities: {current_entities}")
            print(f"   Relationships: {current_relationships}")
        
        # Refresh with improved extraction
        print(f"\n🔄 Refreshing knowledge graph with improved extraction...")
        print("   - Using 400 chunks instead of 200")
        print("   - Increased context limit to 15,000 characters")
        print("   - More comprehensive extraction guidelines")
        print("   - Increased max tokens to 4,000")
        
        kg_data = analyzer.refresh_knowledge_graph(book_id)
        
        if 'error' in kg_data:
            print(f"❌ Error: {kg_data['error']}")
            return
        
        # Show improved results
        entities = kg_data.get('entities', {})
        relationships = kg_data.get('relationships', [])
        
        print(f"\n✅ Improved extraction results:")
        print(f"   📊 Entities: {len(entities)} (was {current_entities if current_kg else 0})")
        print(f"   🔗 Relationships: {len(relationships)} (was {current_relationships if current_kg else 0})")
        
        # Show entity breakdown by type
        entity_types = {}
        for entity in entities.values():
            entity_type = entity.get('type', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        print(f"\n📋 Entity breakdown by type:")
        for entity_type, count in entity_types.items():
            print(f"   - {entity_type}: {count}")
        
        # Show sample entities
        print(f"\n📋 Sample entities:")
        for i, (entity_id, entity) in enumerate(list(entities.items())[:10]):
            importance = entity.get('importance', 0.5)
            print(f"   {i+1}. {entity['name']} ({entity['type']}) - Importance: {importance:.1f}")
        
        # Show sample relationships
        print(f"\n🔗 Sample relationships:")
        for i, rel in enumerate(relationships[:10]):
            from_name = entities[rel['from']]['name']
            to_name = entities[rel['to']]['name']
            strength = rel.get('strength', 0.5)
            print(f"   {i+1}. {from_name} --[{rel['type']}]--> {to_name} (strength: {strength:.1f})")
        
        # Show relationship types
        rel_types = {}
        for rel in relationships:
            rel_type = rel.get('type', 'unknown')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        print(f"\n🔗 Relationship types:")
        for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {rel_type}: {count}")
        
        print(f"\n🎉 Knowledge graph refresh complete!")
        print(f"💡 The force graph visualization will now show much more comprehensive data")
        print(f"🌐 Visit http://localhost:7777/force-graph to see the improved visualization")
        
    except Exception as e:
        print(f"❌ Error during refresh: {e}")
        import traceback
        traceback.print_exc()

def show_current_stats():
    """Show current knowledge graph statistics"""
    print("📊 Current Knowledge Graph Statistics")
    print("=" * 40)
    
    kg_dir = "cache/knowledge_graphs"
    if not os.path.exists(kg_dir):
        print("❌ No knowledge graphs found")
        return
    
    for filename in os.listdir(kg_dir):
        if filename.startswith('kg_') and filename.endswith('.pkl'):
            book_id = filename[3:-4]
            
            try:
                with open(os.path.join(kg_dir, filename), 'rb') as f:
                    data = pickle.load(f)
                
                kg = data.get('knowledge_graph', {})
                entities = kg.get('entities', {})
                relationships = kg.get('relationships', [])
                
                print(f"\n📚 {book_id}:")
                print(f"   Entities: {len(entities)}")
                print(f"   Relationships: {len(relationships)}")
                
                # Show entity types
                entity_types = {}
                for entity in entities.values():
                    entity_type = entity.get('type', 'unknown')
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                
                print(f"   Entity types: {dict(entity_types)}")
                
            except Exception as e:
                print(f"   Error reading {filename}: {e}")

def main():
    """Main function"""
    print("🕸️ Knowledge Graph Refresh Tool")
    print("=" * 50)
    
    # Show current stats
    show_current_stats()
    
    print(f"\n" + "="*50)
    
    # Ask user if they want to refresh
    response = input("\n🔄 Do you want to refresh the knowledge graph with improved extraction? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        refresh_knowledge_graph_manually()
    else:
        print("👋 No refresh performed. Current knowledge graphs remain unchanged.")

if __name__ == "__main__":
    main()
