#!/usr/bin/env python3
"""
Multi-Book Analysis System for RAG
Analyzes multiple books and provides book-specific or combined analysis
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

class MultiBookAnalyzer:
    def __init__(self, openrouter_api_key: Optional[str] = None):
        """
        Initialize the Multi-Book Analyzer with OpenRouter
        
        Args:
            openrouter_api_key: OpenRouter API key
        """
        # Initialize ChromaDB client
        self.chroma_client = chromadb.CloudClient(
            api_key=os.getenv('CHROMADB_API_KEY'),
            tenant=os.getenv('CHROMADB_TENANT'),
            database=os.getenv('CHROMADB_DATABASE')
        )
        
        # Get collection
        self.collection = self.chroma_client.get_collection("multi_book_documents")
        
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
        self.book_analyses = {}  # book_id -> analysis
        self.combined_analysis = None
        
        # Caching configuration
        self.cache_dir = "cache"
        self.cache_expiry_days = 7  # Cache expires after 7 days
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_available_books(self) -> List[Dict[str, Any]]:
        """
        Get list of available books in the collection
        
        Returns:
            List of book information
        """
        try:
            # Get a sample of documents to find book IDs
            all_docs = self.collection.get(limit=300)
            
            if not all_docs['documents']:
                return []
            
            # Find unique book IDs from the sample
            book_ids = set()
            for metadata in all_docs['metadatas']:
                book_ids.add(metadata.get('book_id', 'unknown'))
            
            # Also check for known book IDs that might not be in the sample
            known_book_ids = ['sidetrackkey', 'nonamekey', 'wanda & me - act 1']
            for book_id in known_book_ids:
                try:
                    # Check if this book exists
                    book_docs = self.collection.get(where={'book_id': book_id}, limit=1)
                    if book_docs['documents']:
                        book_ids.add(book_id)
                except:
                    pass
            
            # Get information for each book
            books = []
            for book_id in book_ids:
                try:
                    # Get a sample document for this book
                    book_docs = self.collection.get(where={'book_id': book_id}, limit=1)
                    if book_docs['documents']:
                        metadata = book_docs['metadatas'][0]
                        book_info = {
                            'book_id': book_id,
                            'book_title': metadata.get('book_title', 'Unknown'),
                            'author': metadata.get('author', 'Unknown'),
                            'filename': metadata.get('filename', 'Unknown'),
                            'chunk_count': metadata.get('total_chunks', 0),
                            'total_chunks': metadata.get('total_chunks', 0)
                        }
                        books.append(book_info)
                except Exception as e:
                    print(f"Error getting info for book {book_id}: {e}")
            
            return books
            
        except Exception as e:
            print(f"Error getting available books: {e}")
            return []
    
    def get_book_chunks(self, book_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific book
        
        Args:
            book_id: The book identifier
            
        Returns:
            List of chunks with metadata
        """
        try:
            # Query for specific book
            results = self.collection.get(
                where={"book_id": book_id}
            )
            
            chunks = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    chunk = {
                        'text': doc,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                        'id': results['ids'][i] if results['ids'] else f"chunk_{i}"
                    }
                    chunks.append(chunk)
            
            # Sort by chunk index for chronological order
            chunks.sort(key=lambda x: x.get('metadata', {}).get('chunk_index', 0))
            return chunks
            
        except Exception as e:
            print(f"Error retrieving chunks for book {book_id}: {e}")
            return []
    
    def analyze_single_book(self, book_id: str, force_refresh: bool = False) -> Dict[str, str]:
        """
        Analyze a single book
        
        Args:
            book_id: The book identifier
            force_refresh: Whether to force refresh the analysis
            
        Returns:
            Dictionary with analysis results
        """
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"book_analysis_{book_id}.pkl")
        
        if not force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Check if cache is still valid
                if self.is_cache_valid(cached_data.get('metadata', {})):
                    print(f"📂 Loading cached analysis for {book_id}...")
                    return cached_data['analysis']
            except Exception as e:
                print(f"Error loading cache for {book_id}: {e}")
        
        print(f"🔍 Analyzing book: {book_id}...")
        
        # Get book chunks
        chunks = self.get_book_chunks(book_id)
        if not chunks:
            return {'error': f'No chunks found for book {book_id}'}
        
        # Get book info
        book_info = chunks[0]['metadata']
        book_title = book_info.get('book_title', book_id)
        
        print(f"   Book: {book_title}")
        print(f"   Chunks: {len(chunks)}")
        
        # Sample chunks for analysis (up to 200 chunks)
        total_chunks = len(chunks)
        sample_size = min(200, total_chunks)
        
        sample_chunks = []
        if total_chunks <= sample_size:
            sample_chunks = chunks
        else:
            # Beginning (first 40%)
            sample_chunks.extend(chunks[:total_chunks//2])
            # Middle (middle 40%)
            middle_start = total_chunks//2 - total_chunks//5
            sample_chunks.extend(chunks[middle_start:middle_start + total_chunks//2])
            # End (last 40%)
            sample_chunks.extend(chunks[-total_chunks//2:])
        
        # Create context for analysis
        context_parts = []
        for i, chunk in enumerate(sample_chunks):
            metadata = chunk.get('metadata', {})
            chunk_index = metadata.get('chunk_index', i)
            context_parts.append(f"--- Section {i+1} (chunk {chunk_index}) ---")
            context_parts.append(chunk['text'])
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Perform analysis
        analysis = {}
        
        # 1. Book Summary
        print(f"   📖 Creating summary...")
        analysis['book_summary'] = self.create_book_summary(book_title, context)
        
        # 2. Character Analysis
        print(f"   👥 Analyzing characters...")
        analysis['character_analysis'] = self.analyze_characters(book_id, context)
        
        # 3. Plot Analysis
        print(f"   📚 Analyzing plot...")
        analysis['plot_analysis'] = self.analyze_plot_and_conflicts(book_id, context)
        
        # Cache the analysis
        cache_data = {
            'analysis': analysis,
            'metadata': {
                'book_id': book_id,
                'book_title': book_title,
                'created_at': datetime.now().isoformat(),
                'model': self.model,
                'chunks_analyzed': len(sample_chunks),
                'total_chunks': total_chunks
            }
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"   💾 Analysis cached for {book_id}")
        except Exception as e:
            print(f"   ⚠️ Could not cache analysis: {e}")
        
        return analysis
    
    def create_book_summary(self, book_title: str, context: str) -> str:
        """Create a comprehensive summary of a book"""
        summary_prompt = f"""Based on the following extensive excerpts from the book "{book_title}", create a comprehensive, detailed summary that includes:

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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error creating summary: {e}"
    
    def analyze_characters(self, book_id: str, context: str) -> str:
        """Analyze characters in a book"""
        analysis_prompt = f"""Based on the following extensive content from the book, provide a comprehensive, detailed character analysis including:

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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing characters: {e}"
    
    def analyze_plot_and_conflicts(self, book_id: str, context: str) -> str:
        """Analyze plot and conflicts in a book"""
        analysis_prompt = f"""Based on the following content from the book, provide a comprehensive plot and conflict analysis including:

1. **Plot Structure**: 
   - Beginning, middle, and end
   - Major turning points and climax
   - Story arc and narrative progression
   - Pacing and tension

2. **Main Conflicts**: 
   - All major conflicts and their development
   - How conflicts are resolved or persist
   - Impact of conflicts on characters and plot
   - Internal vs external conflicts

3. **Key Events**: 
   - Major events and their significance
   - Cause and effect relationships
   - Consequences of actions
   - Plot twists and revelations

4. **Themes and Motifs**: 
   - Major themes and their development
   - Recurring motifs and symbols
   - Deeper meanings and messages
   - How themes are expressed through plot

5. **Resolution**: 
   - How conflicts are resolved
   - Character outcomes and growth
   - Final state of the story world
   - Open questions or loose ends

Content:
{context}

Provide a detailed analysis of the plot structure, conflicts, and themes."""

        try:
            messages = [
                {"role": "system", "content": "You are a literary analyst specializing in plot and conflict analysis. Be thorough and insightful."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing plot: {e}"
    
    def analyze_all_books(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Analyze all available books
        
        Args:
            force_refresh: Whether to force refresh all analyses
            
        Returns:
            Dictionary with all book analyses
        """
        books = self.get_available_books()
        if not books:
            return {'error': 'No books found'}
        
        print(f"🔍 Analyzing {len(books)} books...")
        
        all_analyses = {}
        for book in books:
            book_id = book['book_id']
            print(f"\n📚 Analyzing: {book['book_title']}")
            
            analysis = self.analyze_single_book(book_id, force_refresh)
            all_analyses[book_id] = {
                'book_info': book,
                'analysis': analysis
            }
        
        # Create combined analysis
        print(f"\n🔗 Creating combined analysis...")
        combined_analysis = self.create_combined_analysis(all_analyses)
        all_analyses['_combined'] = combined_analysis
        
        return all_analyses
    
    def create_combined_analysis(self, all_analyses: Dict[str, Any]) -> Dict[str, str]:
        """Create a combined analysis of all books"""
        # Extract summaries from all books
        summaries = []
        for book_id, data in all_analyses.items():
            if book_id == '_combined':
                continue
            book_info = data['book_info']
            analysis = data['analysis']
            summary = analysis.get('book_summary', '')
            summaries.append(f"=== {book_info['book_title']} ===\n{summary}\n")
        
        combined_context = "\n".join(summaries)
        
        combined_prompt = f"""Based on the following comprehensive analyses of multiple books, create a combined literary analysis that includes:

1. **Comparative Analysis**: 
   - Similarities and differences between the books
   - Common themes and motifs
   - Contrasting approaches to similar subjects

2. **Character Comparisons**: 
   - Similar character types across books
   - Different approaches to character development
   - Relationships and dynamics

3. **Thematic Connections**: 
   - Shared themes and how they're expressed differently
   - Unique themes in each book
   - Overall message or worldview

4. **Literary Techniques**: 
   - Similar or different writing styles
   - Narrative techniques used
   - Literary devices and their effectiveness

5. **Overall Assessment**: 
   - Strengths and weaknesses of each book
   - How the books complement each other
   - Recommendations for readers

Book Analyses:
{combined_context}

Provide a comprehensive comparative analysis that highlights both the individual strengths of each book and their collective significance."""

        try:
            messages = [
                {"role": "system", "content": "You are a literary critic providing comparative analysis of multiple books. Be thorough and insightful."},
                {"role": "user", "content": combined_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return {
                'combined_analysis': response.choices[0].message.content,
                'books_analyzed': len(all_analyses) - 1  # Exclude _combined
            }
            
        except Exception as e:
            return {'error': f'Error creating combined analysis: {e}'}
    
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
    
    def get_analysis_summary(self, book_id: Optional[str] = None) -> str:
        """
        Get a summary of analysis for a specific book or all books
        
        Args:
            book_id: Specific book ID, or None for all books
            
        Returns:
            Analysis summary
        """
        if book_id:
            # Get specific book analysis
            cache_file = os.path.join(self.cache_dir, f"book_analysis_{book_id}.pkl")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data = pickle.load(f)
                    analysis = cached_data['analysis']
                    
                    summary_parts = [
                        f"=== {book_id.upper()} ANALYSIS ===",
                        "",
                        "BOOK SUMMARY:",
                        analysis.get('book_summary', 'Not available')[:1000] + "..." if len(analysis.get('book_summary', '')) > 1000 else analysis.get('book_summary', 'Not available'),
                        "",
                        "CHARACTER ANALYSIS:",
                        analysis.get('character_analysis', 'Not available')[:1000] + "..." if len(analysis.get('character_analysis', '')) > 1000 else analysis.get('character_analysis', 'Not available'),
                        "",
                        "PLOT & CONFLICT ANALYSIS:",
                        analysis.get('plot_analysis', 'Not available')[:1000] + "..." if len(analysis.get('plot_analysis', '')) > 1000 else analysis.get('plot_analysis', 'Not available'),
                        "",
                        "=== END ANALYSIS ==="
                    ]
                    return "\n".join(summary_parts)
                except Exception as e:
                    return f"Error loading analysis for {book_id}: {e}"
            else:
                return f"No analysis found for {book_id}"
        else:
            # Get combined analysis
            books = self.get_available_books()
            if not books:
                return "No books available for analysis"
            
            summary_parts = ["=== MULTI-BOOK ANALYSIS SUMMARY ===", ""]
            
            for book in books:
                book_id = book['book_id']
                book_summary = self.get_analysis_summary(book_id)
                summary_parts.append(book_summary)
                summary_parts.append("")
            
            return "\n".join(summary_parts)

def main():
    """Main function to test multi-book analysis"""
    print("🚀 Multi-Book Analysis System")
    print("=" * 50)
    
    analyzer = MultiBookAnalyzer()
    
    # List available books
    books = analyzer.get_available_books()
    print(f"📚 Available books: {len(books)}")
    for book in books:
        print(f"   - {book['book_title']} ({book['chunk_count']} chunks)")
    
    if books:
        print(f"\n🔍 Analyzing all books...")
        result = analyzer.analyze_all_books()
        
        if 'error' not in result:
            print(f"✅ Analysis complete!")
            print(f"📊 Books analyzed: {len(result) - 1}")  # Exclude _combined
        else:
            print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()
