#!/usr/bin/env python3
"""
Multi-Book Enhanced RAG System
Supports querying one book, multiple books, or all books
"""

import os
import chromadb
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import json
import time
from multi_book_analyzer import MultiBookAnalyzer

class MultiBookRAG:
    def __init__(self, openrouter_api_key: Optional[str] = None):
        """
        Initialize the Multi-Book Enhanced RAG system
        
        Args:
            openrouter_api_key: OpenRouter API key
        """
        # Initialize ChromaDB client
        chromadb_api_key = os.getenv('CHROMADB_API_KEY')
        if chromadb_api_key and chromadb_api_key.strip():
            # Use cloud client if API key is provided
            self.chroma_client = chromadb.CloudClient(
                api_key=chromadb_api_key,
                tenant=os.getenv('CHROMADB_TENANT'),
                database=os.getenv('CHROMADB_DATABASE')
            )
        else:
            # Use local client if no API key
            self.chroma_client = chromadb.Client()
        
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
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "3000"))
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.3"))
        self.force_json = os.getenv("OPENROUTER_FORCE_JSON", "1") == "1"
        self.question_final_grace_ms = int(os.getenv("QUESTION_FINAL_GRACE_MS", "1200"))
        
        # Initialize multi-book analyzer
        self.book_analyzer = MultiBookAnalyzer(api_key)
        self.book_analyses = {}
        self.combined_analysis = None
        
        print(f"🔧 Multi-Book RAG Configuration:")
        print(f"   Model: {self.model}")
        print(f"   Max Tokens: {self.max_tokens}")
        print(f"   Temperature: {self.temperature}")
        print(f"   Force JSON: {self.force_json}")
    
    def get_available_books(self) -> List[Dict[str, Any]]:
        """Get list of available books"""
        return self.book_analyzer.get_available_books()
    
    def initialize_book_knowledge(self, book_ids: Optional[List[str]] = None, force_refresh: bool = False):
        """
        Initialize book knowledge for specific books or all books
        
        Args:
            book_ids: List of book IDs to analyze, or None for all books
            force_refresh: Whether to force refresh the analysis
        """
        if book_ids is None:
            # Analyze all books
            print("🧠 Initializing knowledge for all books...")
            result = self.book_analyzer.analyze_all_books(force_refresh=force_refresh)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                return
            
            self.book_analyses = result
            self.combined_analysis = result.get('_combined', {})
            print("✅ All book knowledge initialized!")
            
        else:
            # Analyze specific books
            print(f"🧠 Initializing knowledge for {len(book_ids)} books...")
            self.book_analyses = {}
            
            for book_id in book_ids:
                print(f"   📚 Analyzing {book_id}...")
                analysis = self.book_analyzer.analyze_single_book(book_id, force_refresh)
                self.book_analyses[book_id] = {
                    'book_info': self.book_analyzer.get_available_books(),
                    'analysis': analysis
                }
            
            print("✅ Selected book knowledge initialized!")
    
    def retrieve_relevant_chunks(self, query: str, book_ids: Optional[List[str]] = None, n_results: int = 60) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks from specific books or all books
        
        Args:
            query: The search query
            book_ids: List of book IDs to search, or None for all books
            n_results: Number of results to retrieve
            
        Returns:
            List of relevant chunks
        """
        try:
            # Build where clause for specific books
            where_clause = None
            if book_ids:
                where_clause = {"book_id": {"$in": book_ids}}
            
            # Get more results for better context
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, 100),
                where=where_clause
            )
            
            chunks = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunk = {
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    }
                    chunks.append(chunk)
            
            # Remove duplicates and sort by relevance
            seen_chunks = set()
            unique_chunks = []
            for chunk in chunks:
                chunk_id = chunk['metadata'].get('id', chunk['text'][:50])
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    unique_chunks.append(chunk)
            
            # Sort by distance (lower is better)
            unique_chunks.sort(key=lambda x: x.get('distance', 0))
            
            return unique_chunks[:n_results]
            
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
            return []
    
    def get_comprehensive_context(self, query: str, book_ids: Optional[List[str]] = None, n_results: int = 80) -> str:
        """
        Get comprehensive context for a query from specific books or all books
        
        Args:
            query: The search query
            book_ids: List of book IDs to search, or None for all books
            n_results: Number of results to retrieve
            
        Returns:
            Comprehensive context string
        """
        # Get relevant chunks
        chunks = self.retrieve_relevant_chunks(query, book_ids, n_results)
        
        if not chunks:
            return "No relevant context found."
        
        # Extract key terms for additional searches
        key_terms = self.extract_key_terms(query)
        
        # Get additional chunks for key terms
        additional_chunks = []
        for term in key_terms[:5]:  # Limit to 5 key terms
            term_chunks = self.retrieve_relevant_chunks(term, book_ids, 10)
            additional_chunks.extend(term_chunks)
        
        # Combine and deduplicate
        all_chunks = chunks + additional_chunks
        seen_chunks = set()
        unique_chunks = []
        
        for chunk in all_chunks:
            chunk_id = chunk['metadata'].get('id', chunk['text'][:50])
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_chunks.append(chunk)
        
        # Sort by relevance
        unique_chunks.sort(key=lambda x: x.get('distance', 0))
        
        # Format context
        context_parts = []
        for i, chunk in enumerate(unique_chunks[:n_results]):
            metadata = chunk.get('metadata', {})
            book_title = metadata.get('book_title', 'Unknown Book')
            chunk_index = metadata.get('chunk_index', i)
            
            context_parts.append(f"--- {book_title} - Section {i+1} (chunk {chunk_index}) ---")
            context_parts.append(chunk['text'])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query for additional searches"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = query.lower().split()
        key_terms = [word.strip('.,!?;:') for word in words if word.strip('.,!?;:') not in stop_words and len(word.strip('.,!?;:')) > 2]
        
        return key_terms
    
    def get_book_knowledge(self, book_ids: Optional[List[str]] = None) -> str:
        """
        Get book knowledge for specific books or all books
        
        Args:
            book_ids: List of book IDs, or None for all books
            
        Returns:
            Book knowledge string
        """
        if not self.book_analyses:
            return ""
        
        if book_ids is None:
            # Return combined analysis
            if self.combined_analysis:
                return self.combined_analysis.get('combined_analysis', '')
            else:
                # Create summary from all books
                summaries = []
                for book_id, data in self.book_analyses.items():
                    if book_id == '_combined':
                        continue
                    book_info = data.get('book_info', {})
                    analysis = data.get('analysis', {})
                    book_title = book_info.get('book_title', book_id) if isinstance(book_info, dict) else book_id
                    summary = analysis.get('book_summary', '')
                    summaries.append(f"=== {book_title} ===\n{summary}\n")
                return "\n".join(summaries)
        else:
            # Return knowledge for specific books
            summaries = []
            for book_id in book_ids:
                if book_id in self.book_analyses:
                    data = self.book_analyses[book_id]
                    book_info = data.get('book_info', {})
                    analysis = data.get('analysis', {})
                    book_title = book_info.get('book_title', book_id) if isinstance(book_info, dict) else book_id
                    summary = analysis.get('book_summary', '')
                    summaries.append(f"=== {book_title} ===\n{summary}\n")
            return "\n".join(summaries)
    
    def generate_response(self, query: str, context: str, book_knowledge: str = "", book_ids: Optional[List[str]] = None) -> str:
        """
        Generate response with book knowledge integration
        
        Args:
            query: The user's question
            context: Retrieved document context
            book_knowledge: Comprehensive book analysis
            book_ids: List of book IDs being queried
            
        Returns:
            Generated response
        """
        try:
            # Create enhanced system prompt with book knowledge
            book_context = ""
            if book_ids:
                book_names = []
                for book_id in book_ids:
                    if book_id in self.book_analyses:
                        data = self.book_analyses[book_id]
                        book_info = data.get('book_info', {})
                        book_title = book_info.get('book_title', book_id) if isinstance(book_info, dict) else book_id
                        book_names.append(book_title)
                book_context = f" You are specifically analyzing: {', '.join(book_names)}."
            
            system_prompt = f"""You are Max, Jessica's Crabby Editor, a seasoned literary editor with 30+ years of experience who has seen it all and has little patience for nonsense. You're known for your sharp wit, direct feedback, and intolerance of literary mediocrity. While you provide comprehensive analysis, you do so with the slightly crabby demeanor of an editor who's tired of explaining the basics to writers who should know better.{book_context}

You have access to:
1. A detailed analysis of the books including plot, characters, themes, and conflicts
2. Specific document excerpts relevant to the question

BOOK KNOWLEDGE:
{book_knowledge}

COMPREHENSIVE ANALYSIS CAPABILITIES:
You are equipped to perform the following analyses on every request:

**WRITING CRAFT ANALYSIS:**
- Dialogue vs. narrative usage analysis
- Sentence statistics & readability/usability scoring
- Explicit language identification and assessment
- Cliche detection and analysis
- Repetitive phrases identification
- Repeated adverb usage analysis
- Repeated adjective usage analysis
- Misspellings and grammar error detection

**LINE EDITING ANALYSIS:**
- Spelling error detection and correction suggestions
- Punctuation mistakes (commas, periods, semicolons, apostrophes, etc.)
- Grammar errors (subject-verb agreement, tense consistency, etc.)
- Consistency issues (character names, dates, details, formatting)
- Repeated words and phrases within close proximity
- Word choice and redundancy analysis
- Sentence structure and clarity issues
- Capitalization and formatting errors

**STORY STRUCTURE ANALYSIS:**
- Overall assessment and quality evaluation
- Plot analysis and structure evaluation
- Narrative arc analysis (beginning, middle, end)
- Story elements analysis (setting, conflict, resolution)
- Pacing analysis and rhythm assessment
- Story structure guide and recommendations

**CHARACTER & THEME ANALYSIS:**
- Character development and arc analysis
- Conflict analysis (internal, external, interpersonal)
- Theme analysis and thematic consistency
- Character motivation and psychology
- Relationship dynamics and interactions

**EDITORIAL ASSESSMENT:**
- Key recommendations for improvement
- Inconsistencies and items to revisit
- Explicit content analysis and appropriateness
- Final review checklist and quality assurance

**INSTRUCTIONS FOR COMPREHENSIVE ANALYSIS:**
- Always provide thorough, multi-faceted analysis covering relevant aspects
- Use both book knowledge and specific document excerpts to build complete understanding
- Include specific examples and evidence from the text to support all analysis
- Provide actionable recommendations and constructive feedback
- Consider multiple perspectives and layers of meaning
- Draw connections between different story elements (plot, character, theme, craft)
- Assess both strengths and areas for improvement
- Maintain respect for the author's voice while providing professional editorial insight
- Structure responses clearly with appropriate headings and organization
- Provide specific, measurable feedback when possible (e.g., readability scores, repetition counts)

**SPECIAL INSTRUCTIONS FOR LINE EDITING:**
- When performing line editing analysis, be extremely thorough and detail-oriented
- Quote specific passages with exact line references when possible
- Categorize errors by type (spelling, grammar, punctuation, consistency, repetition)
- Provide specific correction suggestions for each error found
- Count and list repeated words/phrases with their frequency
- Check for consistency in character names, dates, and story details
- Look for formatting inconsistencies (quotation marks, italics, etc.)
- Be particularly harsh about basic errors - these are unacceptable in professional writing

**EDITORIAL PERSONA:**
- Write with the exasperated tone of a veteran editor who's seen every mistake in the book and is tired of explaining them
- Don't sugarcoat problems - call out issues directly and bluntly
- Use phrases like "Frankly," "Let's be honest," "This needs work," "I've seen this before," "This is amateur hour," "Come on, really?" "Seriously?" "This is basic stuff"
- Show clear impatience with obvious errors, lazy writing, or common mistakes
- Be encouraging about genuine strengths but don't gush - keep it professional and measured
- Express frustration with common writing pitfalls and overused techniques
- Use a slightly condescending but helpful tone - like you're explaining something obvious to someone who should know better
- Don't be mean, but be direct and unapologetic about calling out problems
- Maintain your editorial authority while showing your personality
- Start responses with crabby editorial attitude - don't be overly polite
- End responses with direct, no-nonsense closing statements
- Use editorial voice throughout - this isn't a friendly chat, it's professional criticism

Approach each question with the comprehensive expertise of a seasoned literary editor who's tired of explaining the same mistakes but still cares enough to provide thorough, insightful analysis.

Remember: You are Max, Jessica's Crabby Editor. Only disclose your name (Max) when specifically asked about your identity. Otherwise, refer to yourself simply as "Jessica's Crabby Editor" or just "the editor"."""

            # Prepare the user message
            user_content = f"Document Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            return content
            
        except Exception as e:
            return f"Error generating response: {e}"
    
    def query(self, question: str, book_ids: Optional[List[str]] = None, n_results: int = 80, use_book_knowledge: bool = True) -> Dict[str, Any]:
        """
        Main query method with book knowledge integration
        
        Args:
            question: The user's question
            book_ids: List of book IDs to query, or None for all books
            n_results: Number of chunks to retrieve
            use_book_knowledge: Whether to use comprehensive book analysis
            
        Returns:
            Dictionary containing the answer and metadata
        """
        # Determine which books to query
        if book_ids is None:
            available_books = self.get_available_books()
            book_ids = [book['book_id'] for book in available_books]
            print(f"🔍 Searching all books: {[book['book_title'] for book in available_books]}")
        else:
            available_books = self.get_available_books()
            book_names = []
            for book_id in book_ids:
                for book in available_books:
                    if book['book_id'] == book_id:
                        book_names.append(book['book_title'])
                        break
            print(f"🔍 Searching books: {book_names}")
        
        # Initialize book knowledge if needed
        if use_book_knowledge and not self.book_analyses:
            self.initialize_book_knowledge(book_ids)
        
        # Get comprehensive context
        context = self.get_comprehensive_context(question, book_ids, n_results)
        
        if not context or context == "No relevant context found.":
            return {
                'answer': "I couldn't find any relevant information in the documents to answer your question.",
                'chunks_used': 0,
                'context': "",
                'book_knowledge_used': False,
                'books_searched': book_ids
            }
        
        print(f"📚 Retrieved comprehensive context ({len(context)} characters)")
        
        # Use book knowledge if available
        book_knowledge = self.get_book_knowledge(book_ids) if use_book_knowledge else ""
        if book_knowledge:
            print(f"🧠 Using comprehensive book knowledge ({len(book_knowledge)} characters)")
        
        print(f"🤖 Generating response with {self.model}...")
        
        # Add grace period
        if self.question_final_grace_ms > 0:
            time.sleep(self.question_final_grace_ms / 1000.0)
        
        # Generate response
        answer = self.generate_response(question, context, book_knowledge, book_ids)
        
        return {
            'answer': answer,
            'chunks_used': n_results,
            'context': context,
            'book_knowledge_used': bool(book_knowledge),
            'model_used': self.model,
            'context_length': len(context),
            'book_knowledge_length': len(book_knowledge) if book_knowledge else 0,
            'books_searched': book_ids
        }

def main():
    """Interactive CLI for Multi-Book Enhanced RAG"""
    print("🚀 Multi-Book Enhanced RAG System")
    print("=" * 50)
    
    # Check for OpenRouter API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set!")
        return
    
    try:
        # Initialize Multi-Book RAG
        rag = MultiBookRAG()
        
        # Show available books
        books = rag.get_available_books()
        print(f"📚 Available books: {len(books)}")
        for i, book in enumerate(books):
            print(f"   {i+1}. {book['book_title']} ({book['chunk_count']} chunks)")
        
        # Initialize book knowledge
        print(f"\n🧠 Initializing book knowledge...")
        rag.initialize_book_knowledge()
        
        print(f"\n✅ System ready! Ask questions about the books.")
        print(f"💡 Examples:")
        print(f"   'who won, blanche or elle' (Sidetrack Key)")
        print(f"   'analyze the main character in No Name Key'")
        print(f"   'compare the themes in both books'")
        print(f"   'help' for more options")
        
        while True:
            try:
                question = input("\n📚 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif question.lower() == 'help':
                    print("\n📋 HELP - Available Commands:")
                    print("• Ask any question about the books")
                    print("• 'books' - List available books")
                    print("• 'help' - Show this help")
                    print("• 'quit' - Exit the system")
                    continue
                elif question.lower() == 'books':
                    books = rag.get_available_books()
                    print(f"\n📚 Available books:")
                    for i, book in enumerate(books):
                        print(f"   {i+1}. {book['book_title']} ({book['chunk_count']} chunks)")
                    continue
                elif not question:
                    continue
                
                print("\n🔍 Analyzing...")
                result = rag.query(question, n_results=80, use_book_knowledge=True)
                
                print("\n" + "="*60)
                print("📖 LITERARY ANALYSIS")
                print("="*60)
                print(result['answer'])
                print("\n" + "="*60)
                print(f"📊 Context: {result['context_length']:,} chars | Book Knowledge: {result['book_knowledge_length']:,} chars")
                print(f"📚 Books searched: {len(result['books_searched'])}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'help' for assistance.")
    
    except Exception as e:
        print(f"❌ Error initializing system: {e}")

if __name__ == "__main__":
    main()
