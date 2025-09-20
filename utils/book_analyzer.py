#!/usr/bin/env python3
"""
Comprehensive Book Analysis System for RAG
"""

import os
import chromadb
from typing import List, Dict, Any, Optional
from openai import OpenAI
import json
import time
import pickle
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict

class BookAnalyzer:
    def __init__(self, openrouter_api_key: Optional[str] = None):
        """
        Initialize the Book Analyzer with OpenRouter
        
        Args:
            openrouter_api_key: OpenRouter API key
        """
        # Initialize ChromaDB client
        self.chroma_client = chromadb.CloudClient(
            api_key='ck-3ZYHJbV3rG3Cw6Xx8dxBDXR7KvSEPUcdACWGbjMueSwo',
            tenant='d92a3881-247b-4e1c-913c-9a361d3c1ade',
            database='bunny'
        )
        
        # Get collection
        self.collection = self.chroma_client.get_collection("bunny_documents")
        
        # Initialize OpenRouter client
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # Configuration
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.3"))
        self.force_json = os.getenv("OPENROUTER_FORCE_JSON", "1") == "1"
        
        # Book analysis cache
        self.book_summary = None
        self.character_analysis = None
        self.plot_analysis = None
        self.themes_analysis = None
        
        # Caching configuration
        self.cache_dir = "cache"
        self.cache_file = os.path.join(self.cache_dir, "book_analysis.pkl")
        self.cache_metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        self.cache_expiry_days = 7  # Cache expires after 7 days
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_hash(self) -> str:
        """
        Generate a hash based on the collection content for cache validation
        
        Returns:
            Hash string representing the current state of the collection
        """
        try:
            # Get collection info to create a hash
            count = self.collection.count()
            # Get a sample of document IDs to create a content hash
            sample_results = self.collection.get(limit=10)
            sample_ids = sample_results.get('ids', [])
            
            # Create hash from count and sample IDs
            content_string = f"{count}_{'_'.join(sample_ids[:5])}"
            return hashlib.md5(content_string.encode()).hexdigest()
        except Exception as e:
            print(f"Warning: Could not generate cache hash: {e}")
            return "unknown"
    
    def is_cache_valid(self) -> bool:
        """
        Check if the cached analysis is still valid
        
        Returns:
            True if cache is valid, False otherwise
        """
        try:
            if not os.path.exists(self.cache_file) or not os.path.exists(self.cache_metadata_file):
                return False
            
            # Load cache metadata
            with open(self.cache_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if cache has expired
            cache_time = datetime.fromisoformat(metadata['created_at'])
            if datetime.now() - cache_time > timedelta(days=self.cache_expiry_days):
                print("📅 Cache has expired")
                return False
            
            # Check if content has changed
            current_hash = self.get_cache_hash()
            if metadata.get('content_hash') != current_hash:
                print("📝 Content has changed, cache invalid")
                return False
            
            print("✅ Cache is valid")
            return True
            
        except Exception as e:
            print(f"⚠️ Error checking cache validity: {e}")
            return False
    
    def save_analysis_to_cache(self, analysis: Dict[str, str]):
        """
        Save the analysis to cache
        
        Args:
            analysis: Dictionary containing the analysis results
        """
        try:
            # Save analysis data
            with open(self.cache_file, 'wb') as f:
                pickle.dump(analysis, f)
            
            # Save metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'content_hash': self.get_cache_hash(),
                'model': self.model,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'force_json': self.force_json,
                'analysis_keys': list(analysis.keys())
            }
            
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 Analysis saved to cache ({len(analysis)} components)")
            
        except Exception as e:
            print(f"❌ Error saving cache: {e}")
    
    def load_analysis_from_cache(self) -> Optional[Dict[str, str]]:
        """
        Load the analysis from cache
        
        Returns:
            Dictionary containing cached analysis or None if not available
        """
        try:
            if not self.is_cache_valid():
                return None
            
            with open(self.cache_file, 'rb') as f:
                analysis = pickle.load(f)
            
            print(f"📂 Analysis loaded from cache ({len(analysis)} components)")
            return analysis
            
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
            return None
    
    def clear_cache(self):
        """Clear the analysis cache"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            if os.path.exists(self.cache_metadata_file):
                os.remove(self.cache_metadata_file)
            print("🗑️ Cache cleared")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the current cache
        
        Returns:
            Dictionary with cache information
        """
        try:
            if not os.path.exists(self.cache_metadata_file):
                return {'status': 'no_cache'}
            
            with open(self.cache_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            cache_time = datetime.fromisoformat(metadata['created_at'])
            age = datetime.now() - cache_time
            
            return {
                'status': 'valid' if self.is_cache_valid() else 'invalid',
                'created_at': metadata['created_at'],
                'age_days': age.days,
                'age_hours': age.seconds // 3600,
                'model': metadata.get('model'),
                'analysis_keys': metadata.get('analysis_keys', []),
                'content_hash': metadata.get('content_hash')
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
        
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks from the book for comprehensive analysis
        
        Returns:
            List of all chunks with metadata
        """
        try:
            # Get all documents (we know there are 545 chunks)
            all_results = self.collection.get()
            
            chunks = []
            if all_results['documents']:
                for i, doc in enumerate(all_results['documents']):
                    chunk = {
                        'text': doc,
                        'metadata': all_results['metadatas'][i] if all_results['metadatas'] else {},
                        'id': all_results['ids'][i] if all_results['ids'] else f"chunk_{i}"
                    }
                    chunks.append(chunk)
            
            # Sort by chunk index for chronological order
            chunks.sort(key=lambda x: x.get('metadata', {}).get('chunk_index', 0))
            return chunks
            
        except Exception as e:
            print(f"Error retrieving all chunks: {e}")
            return []
    
    def create_book_summary(self) -> str:
        """
        Create a comprehensive summary of the entire book
        
        Returns:
            Book summary string
        """
        print("📖 Creating comprehensive book summary...")
        
        all_chunks = self.get_all_chunks()
        if not all_chunks:
            return "No book content found."
        
        # Sample chunks from different parts of the book for summary
        total_chunks = len(all_chunks)
        sample_size = min(200, total_chunks)  # Doubled to 200 chunks for much more comprehensive analysis
        
        # Get chunks from beginning, middle, and end
        sample_chunks = []
        if total_chunks <= sample_size:
            sample_chunks = all_chunks
        else:
            # Beginning (first 40%)
            sample_chunks.extend(all_chunks[:total_chunks//2])
            # Middle (middle 40%)
            middle_start = total_chunks//2 - total_chunks//5
            sample_chunks.extend(all_chunks[middle_start:middle_start + total_chunks//2])
            # End (last 40%)
            sample_chunks.extend(all_chunks[-total_chunks//2:])
        
        # Create context for summary
        context_parts = []
        for i, chunk in enumerate(sample_chunks):
            metadata = chunk.get('metadata', {})
            chunk_index = metadata.get('chunk_index', i)
            context_parts.append(f"--- Section {i+1} (chunk {chunk_index}) ---")
            context_parts.append(chunk['text'])
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Generate comprehensive summary
        summary_prompt = f"""Based on the following extensive excerpts from the book "Sidetrack Key", create a comprehensive, detailed summary that includes:

1. **Plot Overview**: Complete story arc, all major events, narrative structure, and story progression
2. **Main Characters**: Detailed analysis of primary characters including:
   - Physical descriptions and personalities
   - Character arcs and development throughout the story
   - Relationships between characters
   - Motivations and conflicts
   - Character growth and changes
3. **Supporting Characters**: Secondary characters and their roles in the story
4. **Setting**: Detailed time period, location, atmosphere, and environmental factors
5. **Themes**: Major themes, motifs, symbols, and deeper meanings
6. **Key Conflicts**: All major conflicts, their development, resolution, and impact
7. **Story Structure**: Detailed beginning, middle, end, major turning points, and climax
8. **Literary Elements**: Writing style, narrative techniques, and literary devices
9. **Character Relationships**: Complex relationships, dynamics, and interactions
10. **Symbolism and Metaphors**: Key symbols and their meanings

Book Content:
{context}

Please provide an extremely detailed, comprehensive summary that captures the complete essence, depth, and complexity of the entire book. This should be thorough enough to serve as a complete reference for literary analysis."""

        try:
            messages = [
                {"role": "system", "content": "You are a literary analyst creating comprehensive book summaries. Be thorough and detailed."},
                {"role": "user", "content": summary_prompt}
            ]
            
            if self.force_json:
                messages[1]["content"] += " Please provide your response in JSON format with fields: plot_overview, main_characters, setting, themes, key_conflicts, story_structure."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens * 2,  # Use more tokens for summary
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            if self.force_json:
                try:
                    json_response = json.loads(content)
                    return json.dumps(json_response, indent=2)
                except json.JSONDecodeError:
                    return content
            else:
                return content
                
        except Exception as e:
            return f"Error creating book summary: {e}"
    
    def analyze_characters(self) -> str:
        """
        Analyze all characters in the book
        
        Returns:
            Character analysis string
        """
        print("👥 Analyzing characters...")
        
        # Search for character-related content with more comprehensive queries
        character_queries = [
            "main characters",
            "character names",
            "protagonist",
            "antagonist",
            "relationships",
            "character development",
            "Elle",
            "Blanche",
            "character motivations",
            "character conflicts",
            "character dialogue",
            "character actions",
            "character thoughts",
            "character emotions",
            "character background",
            "character personality"
        ]
        
        all_character_chunks = []
        for query in character_queries:
            results = self.collection.query(
                query_texts=[query],
                n_results=30  # Doubled to 30 results per query for much more comprehensive analysis
            )
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunk = {
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    }
                    all_character_chunks.append(chunk)
        
        # Remove duplicates and sort by relevance
        seen_chunks = set()
        unique_chunks = []
        for chunk in all_character_chunks:
            chunk_id = chunk.get('metadata', {}).get('chunk_index', 0)
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_chunks.append(chunk)
        
        unique_chunks.sort(key=lambda x: x['distance'])
        
        # Create context
        context_parts = []
        for i, chunk in enumerate(unique_chunks[:30]):  # Use top 30 chunks
            metadata = chunk.get('metadata', {})
            chunk_index = metadata.get('chunk_index', i)
            context_parts.append(f"--- Character Context {i+1} (chunk {chunk_index}) ---")
            context_parts.append(chunk['text'])
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Generate character analysis
        analysis_prompt = f"""Based on the following extensive content from "Sidetrack Key", provide a comprehensive, detailed character analysis including:

1. **Main Characters**: 
   - Complete names, roles, and detailed descriptions
   - Physical appearance and personality traits
   - Background and history
   - Core values and beliefs

2. **Character Relationships**: 
   - Detailed analysis of how characters interact
   - Relationship dynamics and power structures
   - Emotional connections and tensions
   - How relationships evolve throughout the story

3. **Character Development**: 
   - Detailed character arcs and growth
   - Key moments of change and transformation
   - How characters learn and adapt
   - Internal and external conflicts that drive development

4. **Character Motivations**: 
   - Deep analysis of what drives each character
   - Hidden motivations and subconscious desires
   - How motivations change over time
   - Conflicts between different motivations

5. **Character Conflicts**: 
   - All conflicts between characters
   - Internal conflicts within characters
   - How conflicts are resolved or persist
   - Impact of conflicts on character development

6. **Supporting Characters**: 
   - Detailed analysis of secondary characters
   - Their roles in the story and relationships to main characters
   - How they influence the plot and main characters

7. **Character Psychology**: 
   - Psychological depth and complexity
   - Character flaws and strengths
   - How characters handle stress and challenges
   - Mental and emotional states throughout the story

8. **Character Dialogue and Actions**: 
   - How characters speak and what it reveals
   - Key actions and their significance
   - Character choices and their consequences

Content:
{context}

Provide an extremely detailed, comprehensive character analysis that captures the full depth and complexity of all characters in the book."""

        try:
            messages = [
                {"role": "system", "content": "You are a literary analyst specializing in character analysis. Be thorough and insightful."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            if self.force_json:
                messages[1]["content"] += " Please provide your response in JSON format with fields: main_characters, relationships, development, motivations, conflicts, supporting_characters."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens * 2,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            if self.force_json:
                try:
                    json_response = json.loads(content)
                    return json.dumps(json_response, indent=2)
                except json.JSONDecodeError:
                    return content
            else:
                return content
                
        except Exception as e:
            return f"Error analyzing characters: {e}"
    
    def analyze_plot_and_conflicts(self) -> str:
        """
        Analyze the plot structure and conflicts
        
        Returns:
            Plot analysis string
        """
        print("📚 Analyzing plot and conflicts...")
        
        # Search for plot-related content with more comprehensive queries
        plot_queries = [
            "conflict",
            "plot",
            "story",
            "events",
            "resolution",
            "climax",
            "ending",
            "outcome",
            "beginning",
            "middle",
            "turning point",
            "crisis",
            "tension",
            "drama",
            "action",
            "consequence",
            "result",
            "victory",
            "defeat",
            "struggle",
            "challenge",
            "obstacle",
            "problem",
            "solution"
        ]
        
        all_plot_chunks = []
        for query in plot_queries:
            results = self.collection.query(
                query_texts=[query],
                n_results=30  # Doubled to 30 results per query for much more comprehensive analysis
            )
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunk = {
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    }
                    all_plot_chunks.append(chunk)
        
        # Remove duplicates and sort by relevance
        seen_chunks = set()
        unique_chunks = []
        for chunk in all_plot_chunks:
            chunk_id = chunk.get('metadata', {}).get('chunk_index', 0)
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_chunks.append(chunk)
        
        unique_chunks.sort(key=lambda x: x['distance'])
        
        # Create context
        context_parts = []
        for i, chunk in enumerate(unique_chunks[:25]):  # Use top 25 chunks
            metadata = chunk.get('metadata', {})
            chunk_index = metadata.get('chunk_index', i)
            context_parts.append(f"--- Plot Context {i+1} (chunk {chunk_index}) ---")
            context_parts.append(chunk['text'])
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Generate plot analysis
        analysis_prompt = f"""Based on the following content from "Sidetrack Key", provide a comprehensive plot and conflict analysis including:

1. **Main Plot**: The central story and its progression
2. **Key Conflicts**: Major conflicts and their nature
3. **Conflict Resolution**: How conflicts are resolved (or not resolved)
4. **Story Arc**: Beginning, rising action, climax, falling action, resolution
5. **Subplots**: Secondary storylines and their resolution
6. **Outcomes**: Who wins, who loses, and what the final state is

Content:
{context}

Provide a detailed plot and conflict analysis."""

        try:
            messages = [
                {"role": "system", "content": "You are a literary analyst specializing in plot structure and conflict analysis. Be thorough and analytical."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            if self.force_json:
                messages[1]["content"] += " Please provide your response in JSON format with fields: main_plot, key_conflicts, conflict_resolution, story_arc, subplots, outcomes."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens * 2,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            if self.force_json:
                try:
                    json_response = json.loads(content)
                    return json.dumps(json_response, indent=2)
                except json.JSONDecodeError:
                    return content
            else:
                return content
                
        except Exception as e:
            return f"Error analyzing plot: {e}"
    
    def perform_full_analysis(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Perform comprehensive analysis of the entire book with caching
        
        Args:
            force_refresh: Whether to force a fresh analysis even if cache exists
            
        Returns:
            Dictionary containing all analyses
        """
        # Try to load from cache first
        if not force_refresh:
            cached_analysis = self.load_analysis_from_cache()
            if cached_analysis:
                # Load cached analysis into instance variables
                self.book_summary = cached_analysis.get('book_summary')
                self.character_analysis = cached_analysis.get('character_analysis')
                self.plot_analysis = cached_analysis.get('plot_analysis')
                return cached_analysis
        
        print("🔍 Performing comprehensive book analysis...")
        print("This may take a few minutes as we analyze the entire book...")
        
        analysis = {}
        
        # 1. Book Summary
        analysis['book_summary'] = self.create_book_summary()
        self.book_summary = analysis['book_summary']
        
        # 2. Character Analysis
        analysis['character_analysis'] = self.analyze_characters()
        self.character_analysis = analysis['character_analysis']
        
        # 3. Plot and Conflict Analysis
        analysis['plot_analysis'] = self.analyze_plot_and_conflicts()
        self.plot_analysis = analysis['plot_analysis']
        
        # Save to cache
        self.save_analysis_to_cache(analysis)
        
        print("✅ Book analysis complete!")
        return analysis
    
    def get_analysis_summary(self) -> str:
        """
        Get a condensed summary of all analyses for use in queries
        
        Returns:
            Condensed analysis summary
        """
        if not all([self.book_summary, self.character_analysis, self.plot_analysis]):
            return "Book analysis not yet performed. Run perform_full_analysis() first."
        
        summary_parts = [
            "=== BOOK ANALYSIS SUMMARY ===",
            "",
            "BOOK SUMMARY:",
            self.book_summary[:1000] + "..." if len(self.book_summary) > 1000 else self.book_summary,
            "",
            "CHARACTER ANALYSIS:",
            self.character_analysis[:1000] + "..." if len(self.character_analysis) > 1000 else self.character_analysis,
            "",
            "PLOT & CONFLICT ANALYSIS:",
            self.plot_analysis[:1000] + "..." if len(self.plot_analysis) > 1000 else self.plot_analysis,
            "",
            "=== END ANALYSIS ==="
        ]
        
        return "\n".join(summary_parts)

def main():
    """Test the book analyzer"""
    print("📚 Book Analyzer Test")
    print("="*50)
    
    # Setup environment
    from setup_openrouter import setup_openrouter_env
    setup_openrouter_env()
    
    try:
        analyzer = BookAnalyzer()
        
        # Perform full analysis
        analysis = analyzer.perform_full_analysis()
        
        print("\n" + "="*60)
        print("ANALYSIS RESULTS:")
        print("="*60)
        
        for key, value in analysis.items():
            print(f"\n{key.upper().replace('_', ' ')}:")
            print("-" * 40)
            print(value[:500] + "..." if len(value) > 500 else value)
        
        print("\n" + "="*60)
        print("✅ Analysis complete! Use this knowledge for better RAG queries.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
