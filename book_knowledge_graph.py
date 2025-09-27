#!/usr/bin/env python3
"""
Book Knowledge Graph System
Extracts and stores entities and relationships from books for force graph visualization
"""

import os
import json
import chromadb
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import pickle
from openai import OpenAI

class BookKnowledgeGraph:
    def __init__(self, chroma_client, openrouter_api_key: Optional[str] = None):
        """
        Initialize the Book Knowledge Graph system
        
        Args:
            chroma_client: ChromaDB client instance
            openrouter_api_key: OpenRouter API key for LLM calls
        """
        self.chroma_client = chroma_client
        self.cache_dir = "cache"
        self.kg_dir = os.path.join(self.cache_dir, "knowledge_graphs")
        os.makedirs(self.kg_dir, exist_ok=True)
        
        # Initialize OpenRouter client for entity extraction
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # Configuration
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "4000"))  # Increased for more comprehensive extraction
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.3"))
        self.cache_expiry_days = 7  # Cache expires after 7 days
        
        # Use ChromaDB for entity embeddings and semantic search
        try:
            self.entities_collection = self.chroma_client.get_or_create_collection("book_entities")
        except:
            self.entities_collection = self.chroma_client.create_collection("book_entities")
        
        # Cache for relationships (fast access)
        self.relationships_cache = {}
        
        print(f"🕸️ Knowledge Graph System initialized")
        print(f"   Model: {self.model}")
        print(f"   Cache directory: {self.kg_dir}")
    
    def extract_knowledge_graph(self, book_id: str, context: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Extract knowledge graph from book content
        
        Args:
            book_id: The book identifier
            context: Book content to analyze
            force_refresh: Whether to force refresh the extraction
            
        Returns:
            Dictionary containing entities and relationships
        """
        # Check cache first
        cache_file = os.path.join(self.kg_dir, f"kg_{book_id}.pkl")
        
        if not force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Check if cache is still valid
                if self.is_cache_valid(cached_data.get('metadata', {})):
                    print(f"📂 Loading cached knowledge graph for {book_id}...")
                    return cached_data['knowledge_graph']
            except Exception as e:
                print(f"Error loading KG cache for {book_id}: {e}")
        
        print(f"🔍 Extracting knowledge graph for {book_id}...")
        
        # Extract entities and relationships using LLM
        kg_data = self._extract_entities_and_relationships(book_id, context)
        
        if not kg_data:
            return {'error': f'Failed to extract knowledge graph for {book_id}'}
        
        # Store in cache
        cache_data = {
            'knowledge_graph': kg_data,
            'metadata': {
                'book_id': book_id,
                'created_at': datetime.now().isoformat(),
                'model': self.model,
                'entity_count': len(kg_data.get('entities', {})),
                'relationship_count': len(kg_data.get('relationships', []))
            }
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"   💾 Knowledge graph cached for {book_id}")
        except Exception as e:
            print(f"   ⚠️ Could not cache knowledge graph: {e}")
        
        # Store entities in ChromaDB for semantic search
        self._store_entities_in_chromadb(book_id, kg_data.get('entities', {}))
        
        return kg_data
    
    def _extract_entities_and_relationships(self, book_id: str, context: str) -> Dict[str, Any]:
        """Extract entities and relationships using LLM"""
        extraction_prompt = f"""Based on the following book content, extract a COMPREHENSIVE knowledge graph including ALL characters, places, objects, events, and their relationships. Be thorough and extract as many entities and relationships as possible.

Return ONLY valid JSON with this exact structure:
{{
    "entities": {{
        "entity_id": {{
            "name": "Entity Name",
            "type": "character|place|object|event|concept",
            "description": "Brief description of the entity",
            "book_id": "{book_id}",
            "importance": 0.8
        }}
    }},
    "relationships": [
        {{
            "from": "entity_id_1",
            "to": "entity_id_2",
            "type": "relationship_type",
            "strength": 0.8,
            "description": "How they are related",
            "book_id": "{book_id}"
        }}
    ]
}}

CRITICAL GUIDELINES - BE EXTREMELY THOROUGH:
- Extract EVERY character mentioned, no matter how minor (family members, friends, strangers, animals, etc.)
- Extract EVERY location mentioned (rooms, buildings, streets, cities, countries, etc.)
- Extract EVERY object mentioned (furniture, tools, gifts, vehicles, etc.)
- Extract EVERY event mentioned (meetings, conversations, actions, memories, etc.)
- Include relationships like: friends_with, family_of, lives_in, works_at, owns, uses, caused_by, happened_at, met_at, talked_to, gave_to, received_from, etc.
- Use descriptive entity IDs (e.g., "wanda_character", "toy_box_object", "highway_place")
- Set importance scores (0.0-1.0) based on how central the entity is to the story
- Set relationship strength (0.0-1.0) based on how strong/important the relationship is
- Include BOTH explicit and implicit relationships
- Extract relationships between ALL entities, not just main characters
- Include temporal relationships (happened_before, happened_after)
- Include emotional relationships (loves, hates, fears, trusts)
- Include physical relationships (near, inside, outside, above, below)
- Include ownership relationships (owns, belongs_to, has)
- Include social relationships (knows, met, talked_to, helped, hurt)

Book Content:
{context[:15000]}  # Increased context limit for more comprehensive extraction

Return ONLY the JSON, no other text."""

        try:
            messages = [
                {"role": "system", "content": "You are an expert at extracting structured knowledge graphs from literary texts. Return only valid JSON."},
                {"role": "user", "content": extraction_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up the response to extract JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            # Parse JSON
            kg_data = json.loads(content)
            
            # Validate structure
            if 'entities' not in kg_data or 'relationships' not in kg_data:
                raise ValueError("Invalid knowledge graph structure")
            
            print(f"   ✅ Extracted {len(kg_data['entities'])} entities and {len(kg_data['relationships'])} relationships")
            return kg_data
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error extracting knowledge graph: {e}")
            return None
    
    def _store_entities_in_chromadb(self, book_id: str, entities: Dict[str, Any]):
        """Store entities in ChromaDB for semantic search"""
        try:
            for entity_id, entity_data in entities.items():
                # Create a document for the entity
                entity_doc = f"Entity: {entity_data['name']}. Type: {entity_data['type']}. Description: {entity_data.get('description', '')}"
                
                # Generate a simple embedding (you could use a proper embedding model here)
                entity_embedding = self._generate_simple_embedding(entity_doc)
                
                # Store in ChromaDB
                self.entities_collection.add(
                    ids=[f"{book_id}_{entity_id}"],
                    documents=[entity_doc],
                    metadatas=[{
                        "entity_id": entity_id,
                        "name": entity_data['name'],
                        "type": entity_data['type'],
                        "book_id": book_id,
                        "importance": entity_data.get('importance', 0.5)
                    }],
                    embeddings=[entity_embedding]
                )
            
            print(f"   💾 Stored {len(entities)} entities in ChromaDB")
            
        except Exception as e:
            print(f"   ⚠️ Error storing entities in ChromaDB: {e}")
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Generate a simple embedding for the text"""
        # This is a placeholder - in production you'd use a proper embedding model
        # For now, create a simple hash-based embedding
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 384-dimensional vector (common embedding size)
        embedding = []
        for i in range(384):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        
        return embedding
    
    def _save_knowledge_graph_to_cache(self, book_id: str, kg_data: Dict[str, Any]):
        """Save knowledge graph data to cache file"""
        try:
            cache_file = f"cache/knowledge_graphs/kg_{book_id}.pkl"
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(kg_data, f)
            
            print(f"   💾 Saved knowledge graph to cache: {len(kg_data.get('entities', {}))} entities, {len(kg_data.get('relationships', []))} relationships")
            
        except Exception as e:
            print(f"   ⚠️ Error saving knowledge graph to cache: {e}")
    
    def get_knowledge_graph(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get cached knowledge graph for a book"""
        cache_file = os.path.join(self.kg_dir, f"kg_{book_id}.pkl")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # The cache file contains the knowledge graph data directly
                if 'entities' in cached_data and 'relationships' in cached_data:
                    return cached_data
            except Exception as e:
                print(f"Error loading knowledge graph for {book_id}: {e}")
        
        return None
    
    def get_force_graph_data(self, book_id: str) -> Dict[str, Any]:
        """Convert knowledge graph to force graph format for visualization"""
        # Use the validation function to ensure clean data
        kg_data = self.validate_and_clean_knowledge_graph(book_id)
        
        if not kg_data:
            return {"nodes": [], "links": []}
        
        # Convert entities to nodes
        nodes = []
        for entity_id, entity_data in kg_data.get('entities', {}).items():
            node = {
                "id": entity_id,
                "name": entity_data['name'],
                "type": entity_data['type'],
                "description": entity_data.get('description', ''),
                "importance": entity_data.get('importance', 0.5),
                "group": entity_data['type']
            }
            nodes.append(node)
        
        # Convert relationships to links (already validated by validate_and_clean_knowledge_graph)
        links = []
        for rel in kg_data.get('relationships', []):
            link = {
                "source": rel['from'],
                "target": rel['to'],
                "type": rel['type'],
                "strength": rel.get('strength', 0.5),
                "description": rel.get('description', '')
            }
            links.append(link)
        
        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "book_id": book_id,
                "node_count": len(nodes),
                "link_count": len(links)
            }
        }
    
    def search_entities(self, query: str, book_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for entities using semantic search"""
        try:
            # Build where clause for specific book
            where_clause = None
            if book_id:
                where_clause = {"book_id": book_id}
            
            # Query ChromaDB
            results = self.entities_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause
            )
            
            entities = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    entity = {
                        'entity_id': metadata.get('entity_id', ''),
                        'name': metadata.get('name', ''),
                        'type': metadata.get('type', ''),
                        'book_id': metadata.get('book_id', ''),
                        'importance': metadata.get('importance', 0.5),
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    }
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            print(f"Error searching entities: {e}")
            return []
    
    def get_entity_relationships(self, entity_id: str, book_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for a specific entity"""
        kg_data = self.get_knowledge_graph(book_id)
        
        if not kg_data:
            return []
        
        relationships = []
        for rel in kg_data.get('relationships', []):
            if rel['from'] == entity_id or rel['to'] == entity_id:
                relationships.append(rel)
        
        return relationships
    
    def is_cache_valid(self, metadata: Dict[str, Any]) -> bool:
        """Check if cache is still valid"""
        if not metadata:
            return False
        
        created_at_str = metadata.get('created_at')
        if not created_at_str:
            return False
        
        try:
            created_at = datetime.fromisoformat(created_at_str)
            expiry_date = created_at + timedelta(days=self.cache_expiry_days)
            return datetime.now() < expiry_date
        except:
            return False
    
    def validate_and_clean_knowledge_graph(self, book_id: str) -> Dict[str, Any]:
        """
        Validate and clean knowledge graph data, removing orphaned relationships
        
        Args:
            book_id: The book identifier
            
        Returns:
            Cleaned knowledge graph data
        """
        kg_data = self.get_knowledge_graph(book_id)
        
        if not kg_data:
            return {'entities': {}, 'relationships': []}
        
        entities = kg_data.get('entities', {})
        relationships = kg_data.get('relationships', [])
        
        # Get all entity IDs
        entity_ids = set(entities.keys())
        
        # Filter out orphaned relationships
        valid_relationships = []
        orphaned_count = 0
        
        for rel in relationships:
            from_node = rel.get('from')
            to_node = rel.get('to')
            
            if from_node in entity_ids and to_node in entity_ids:
                valid_relationships.append(rel)
            else:
                orphaned_count += 1
                print(f"   🧹 Removing orphaned relationship: {from_node} -> {to_node}")
        
        if orphaned_count > 0:
            print(f"   🧹 Cleaned {orphaned_count} orphaned relationships from {book_id}")
            
            # Save the cleaned data back to cache
            cleaned_data = {
                'entities': entities,
                'relationships': valid_relationships
            }
            
            try:
                cache_file = os.path.join(self.kg_dir, f"kg_{book_id}.pkl")
                with open(cache_file, 'wb') as f:
                    pickle.dump(cleaned_data, f)
                print(f"   💾 Saved cleaned knowledge graph for {book_id}")
            except Exception as e:
                print(f"   ⚠️ Error saving cleaned knowledge graph: {e}")
        
        return {
            'entities': entities,
            'relationships': valid_relationships
        }
    

def main():
    """Test the knowledge graph system"""
    print("🕸️ Testing Book Knowledge Graph System")
    print("=" * 50)
    
    # This would be used in integration with your existing system
    print("Knowledge graph system ready for integration!")
    print("Use BookKnowledgeGraph with your existing ChromaDB client and OpenRouter API key.")

if __name__ == "__main__":
    main()
