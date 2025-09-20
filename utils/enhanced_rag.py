#!/usr/bin/env python3
"""
Enhanced RAG System with Book Analysis Integration
"""

import os
import chromadb
from typing import List, Dict, Any, Optional
from openai import OpenAI
import json
import time
from book_analyzer import BookAnalyzer

class EnhancedRAG:
    def __init__(self, openrouter_api_key: Optional[str] = None):
        """
        Initialize the Enhanced RAG system with book analysis
        
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
        self.question_final_grace_ms = int(os.getenv("QUESTION_FINAL_GRACE_MS", "1200"))
        
        # Initialize book analyzer
        self.book_analyzer = BookAnalyzer(api_key)
        self.book_analysis = None
        self.analysis_summary = None
        
        print(f"🔧 Enhanced RAG Configuration:")
        print(f"   Model: {self.model}")
        print(f"   Max Tokens: {self.max_tokens}")
        print(f"   Temperature: {self.temperature}")
        print(f"   Force JSON: {self.force_json}")
    
    def initialize_book_knowledge(self, force_refresh: bool = False):
        """
        Initialize the system with comprehensive book knowledge
        
        Args:
            force_refresh: Whether to force a fresh analysis
        """
        if self.book_analysis is None or force_refresh:
            print("🧠 Initializing book knowledge...")
            
            # Check cache status first
            cache_info = self.book_analyzer.get_cache_info()
            if cache_info.get('status') == 'valid' and not force_refresh:
                print("📂 Loading from cache...")
            else:
                print("This will analyze the entire book for better context...")
            
            self.book_analysis = self.book_analyzer.perform_full_analysis(force_refresh=force_refresh)
            self.analysis_summary = self.book_analyzer.get_analysis_summary()
            
            print("✅ Book knowledge initialized!")
        else:
            print("✅ Using existing book knowledge")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the analysis cache
        
        Returns:
            Dictionary with cache information
        """
        return self.book_analyzer.get_cache_info()
    
    def clear_cache(self):
        """Clear the analysis cache"""
        self.book_analyzer.clear_cache()
        self.book_analysis = None
        self.analysis_summary = None
    
    def retrieve_relevant_chunks(self, query: str, n_results: int = 60) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks with enhanced search strategies
        
        Args:
            query: The search query
            n_results: Number of results to retrieve
            
        Returns:
            List of relevant chunks
        """
        try:
            # Get more results for better context
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, 100)
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
            
            # Sort by distance and take the best ones
            chunks.sort(key=lambda x: x['distance'])
            return chunks[:n_results]
            
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
            return []
    
    def get_comprehensive_context(self, query: str, max_chunks: int = 20) -> str:
        """
        Get comprehensive context using multiple search strategies
        
        Args:
            query: The search query
            max_chunks: Maximum number of chunks to retrieve
            
        Returns:
            Comprehensive context string
        """
        # Strategy 1: Direct query
        chunks1 = self.retrieve_relevant_chunks(query, max_chunks // 3)
        
        # Strategy 2: Extract key terms and search
        key_terms = self.extract_key_terms(query)
        chunks2 = []
        if key_terms:
            for term in key_terms[:3]:
                term_chunks = self.retrieve_relevant_chunks(term, 3)
                chunks2.extend(term_chunks)
        
        # Strategy 3: Search for character interactions and conflicts
        chunks3 = []
        if any(word in query.lower() for word in ['won', 'beat', 'defeat', 'victory', 'conflict', 'fight', 'battle', 'competition', 'outcome', 'result']):
            conflict_terms = ['conflict', 'fight', 'battle', 'competition', 'rivalry', 'win', 'lose', 'victory', 'defeat', 'outcome', 'resolution']
            for term in conflict_terms:
                term_chunks = self.retrieve_relevant_chunks(term, 2)
                chunks3.extend(term_chunks)
        
        # Strategy 4: Search for character names
        for word in query.lower().split():
            if word.isalpha() and len(word) > 2:
                name_chunks = self.retrieve_relevant_chunks(word, 2)
                chunks3.extend(name_chunks)
        
        # Combine and deduplicate
        all_chunks = chunks1 + chunks2 + chunks3
        seen_chunks = set()
        unique_chunks = []
        
        for chunk in all_chunks:
            chunk_id = chunk.get('metadata', {}).get('chunk_index', 0)
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_chunks.append(chunk)
        
        unique_chunks.sort(key=lambda x: x['distance'])
        
        # Format context with better organization
        context_parts = []
        for i, chunk in enumerate(unique_chunks[:max_chunks], 1):
            metadata = chunk.get('metadata', {})
            chunk_index = metadata.get('chunk_index', 0)
            source_file = metadata.get('source_file', 'unknown')
            
            context_parts.append(f"--- Context {i} (from {source_file}, chunk {chunk_index}) ---")
            context_parts.append(chunk['text'])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'who', 'where', 'when', 'why', 'how'}
        
        words = query.lower().split()
        key_terms = [word.strip('.,!?;:') for word in words if word.strip('.,!?;:') not in stop_words and len(word.strip('.,!?;:')) > 2]
        
        return key_terms
    
    def generate_response(self, query: str, context: str, book_knowledge: str = "") -> str:
        """
        Generate response with book knowledge integration
        
        Args:
            query: The user's question
            context: Retrieved document context
            book_knowledge: Comprehensive book analysis
            
        Returns:
            Generated response
        """
        try:
            # Create enhanced system prompt with book knowledge
            system_prompt = f"""You are a literary editor with 30 years of experience, known for your ability to provide concise suggestions while respecting the voice of the author. You have deep, comprehensive knowledge of the book "Sidetrack Key" and are renowned for your thorough, insightful, and nuanced analysis of literature.

You have access to:
1. A detailed analysis of the entire book including plot, characters, themes, and conflicts
2. Specific document excerpts relevant to the question

BOOK KNOWLEDGE:
{book_knowledge}

Instructions for Expert Literary Analysis:
- Provide comprehensive, thoughtful responses that demonstrate deep understanding and editorial expertise
- Use both the book knowledge and specific document excerpts to build a complete picture
- For questions about outcomes, conflicts, or "who won", provide definitive answers with detailed reasoning
- Include multiple perspectives and layers of meaning in your analysis
- Draw connections between different aspects of the story (plot, character development, themes, symbolism)
- Provide specific examples and evidence from the text to support your analysis
- Consider the broader implications and deeper meanings of events and relationships
- For character questions, analyze motivations, growth, relationships, and psychological depth
- For plot questions, explain cause-and-effect relationships, turning points, and narrative structure
- Always ground your answers in the provided evidence while offering insightful interpretation
- Write with the authority of an experienced literary editor who understands both craft and artistry
- When providing suggestions or critiques, be constructive and respectful of the author's voice and intentions
- Focus on practical, actionable insights that demonstrate your editorial expertise

Approach each question as an experienced literary editor would, providing thorough analysis that combines scholarly depth with practical editorial wisdom."""

            # Prepare the user message
            if self.force_json:
                user_content = f"Document Context:\n{context}\n\nQuestion: {query}\n\nPlease provide your answer in JSON format with an 'answer' field, being specific and authoritative based on the book knowledge."
            else:
                user_content = f"Document Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"} if self.force_json else None
            )
            
            content = response.choices[0].message.content
            
            # Handle JSON response
            if self.force_json:
                try:
                    json_response = json.loads(content)
                    # Try to extract the main answer content
                    if 'answer' in json_response:
                        # If answer is a simple string, return it
                        if isinstance(json_response['answer'], str):
                            return json_response['answer']
                        # If answer is complex, format the whole response nicely
                        else:
                            return self.format_complex_json_response(json_response)
                    elif 'response' in json_response:
                        return json_response['response']
                    elif 'content' in json_response:
                        return json_response['content']
                    elif 'suggestions' in json_response:
                        # Handle structured suggestions format
                        return self.format_suggestions_response(json_response)
                    elif 'improvements' in json_response:
                        # Handle improvements format
                        return self.format_list_response(json_response['improvements'])
                    elif isinstance(json_response, list):
                        # Handle list responses
                        return self.format_list_response(json_response)
                    else:
                        # If no standard field, return the whole JSON as formatted text
                        return self.format_complex_json_response(json_response)
                except json.JSONDecodeError:
                    return content
            else:
                return content
            
        except Exception as e:
            return f"Error generating response: {e}"
    
    def format_suggestions_response(self, json_response: Dict[str, Any]) -> str:
        """
        Format a suggestions-style JSON response into readable text
        
        Args:
            json_response: The JSON response containing suggestions
            
        Returns:
            Formatted text response
        """
        if 'suggestions' not in json_response:
            return self.format_json_response(json_response)
        
        suggestions = json_response['suggestions']
        if not isinstance(suggestions, list):
            return self.format_json_response(json_response)
        
        formatted_parts = []
        formatted_parts.append("Based on my analysis of 'Sidetrack Key', here are some areas that could be improved:\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            if isinstance(suggestion, dict):
                aspect = suggestion.get('aspect', f'Area {i}')
                improvement = suggestion.get('improvement', 'No specific improvement suggested')
                formatted_parts.append(f"{i}. **{aspect}**")
                formatted_parts.append(f"   {improvement}\n")
        
        return "\n".join(formatted_parts)
    
    def format_list_response(self, list_response: List[Dict[str, Any]]) -> str:
        """
        Format a list response into readable text
        
        Args:
            list_response: The list response to format
            
        Returns:
            Formatted text response
        """
        formatted_parts = []
        
        # Check if it's a suggestions-style list
        if list_response and isinstance(list_response[0], dict) and 'aspect' in list_response[0]:
            formatted_parts.append("Based on my analysis of 'Sidetrack Key', here are some areas that could be improved:\n")
            
            for i, item in enumerate(list_response, 1):
                aspect = item.get('aspect', f'Area {i}')
                suggestion = item.get('suggestion', item.get('improvement', 'No specific suggestion'))
                formatted_parts.append(f"{i}. **{aspect}**")
                formatted_parts.append(f"   {suggestion}\n")
        else:
            # Generic list formatting
            formatted_parts.append("Analysis Results:\n")
            for i, item in enumerate(list_response, 1):
                if isinstance(item, dict):
                    formatted_parts.append(f"{i}. {item}")
                else:
                    formatted_parts.append(f"{i}. {item}")
        
        return "\n".join(formatted_parts)
    
    def format_json_response(self, json_response: Dict[str, Any]) -> str:
        """
        Format any JSON response into readable text
        
        Args:
            json_response: The JSON response to format
            
        Returns:
            Formatted text response
        """
        formatted_parts = []
        
        for key, value in json_response.items():
            if isinstance(value, list):
                formatted_parts.append(f"**{key.replace('_', ' ').title()}:**")
                for i, item in enumerate(value, 1):
                    if isinstance(item, dict):
                        for sub_key, sub_value in item.items():
                            formatted_parts.append(f"  {i}. {sub_key.replace('_', ' ').title()}: {sub_value}")
                    else:
                        formatted_parts.append(f"  {i}. {item}")
                formatted_parts.append("")
            elif isinstance(value, dict):
                formatted_parts.append(f"**{key.replace('_', ' ').title()}:**")
                for sub_key, sub_value in value.items():
                    formatted_parts.append(f"  • {sub_key.replace('_', ' ').title()}: {sub_value}")
                formatted_parts.append("")
            else:
                formatted_parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(formatted_parts)
    
    def format_complex_json_response(self, json_response: Dict[str, Any]) -> str:
        """
        Format a complex JSON response into readable text, handling nested structures
        
        Args:
            json_response: The complex JSON response dictionary
            
        Returns:
            Formatted text response
        """
        formatted_parts = []
        
        # Handle the main answer first if it exists
        if 'answer' in json_response:
            answer = json_response['answer']
            if isinstance(answer, str):
                formatted_parts.append(answer)
            elif isinstance(answer, dict):
                formatted_parts.append(self._format_nested_dict(answer, "Answer"))
        
        # Handle other sections
        for key, value in json_response.items():
            if key == 'answer':
                continue  # Already handled above
                
            if isinstance(value, dict):
                formatted_parts.append(f"\n**{key.replace('_', ' ').title()}:**")
                formatted_parts.append(self._format_nested_dict(value, ""))
            elif isinstance(value, list):
                formatted_parts.append(f"\n**{key.replace('_', ' ').title()}:**")
                for item in value:
                    if isinstance(item, dict):
                        formatted_parts.append(self._format_nested_dict(item, "• "))
                    else:
                        formatted_parts.append(f"• {item}")
            else:
                formatted_parts.append(f"\n**{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(formatted_parts)
    
    def _format_nested_dict(self, data: Dict[str, Any], prefix: str = "") -> str:
        """
        Helper method to format nested dictionaries
        
        Args:
            data: The dictionary to format
            prefix: Prefix for each line
            
        Returns:
            Formatted text
        """
        formatted_parts = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                formatted_parts.append(f"{prefix}**{key.replace('_', ' ').title()}:**")
                formatted_parts.append(self._format_nested_dict(value, prefix + "  "))
            elif isinstance(value, list):
                formatted_parts.append(f"{prefix}**{key.replace('_', ' ').title()}:**")
                for item in value:
                    if isinstance(item, dict):
                        formatted_parts.append(self._format_nested_dict(item, prefix + "  • "))
                    else:
                        formatted_parts.append(f"{prefix}  • {item}")
            else:
                formatted_parts.append(f"{prefix}**{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(formatted_parts)
    
    def query(self, question: str, n_results: int = 80, use_book_knowledge: bool = True) -> Dict[str, Any]:
        """
        Main query method with book knowledge integration
        
        Args:
            question: The user's question
            n_results: Number of chunks to retrieve
            use_book_knowledge: Whether to use comprehensive book analysis
            
        Returns:
            Dictionary containing the answer and metadata
        """
        print(f"🔍 Searching for relevant information...")
        
        # Initialize book knowledge if needed
        if use_book_knowledge and self.analysis_summary is None:
            self.initialize_book_knowledge()
        
        # Get comprehensive context
        context = self.get_comprehensive_context(question, n_results)
        
        if not context or context == "No relevant context found.":
            return {
                'answer': "I couldn't find any relevant information in the documents to answer your question.",
                'chunks_used': 0,
                'context': "",
                'book_knowledge_used': False
            }
        
        print(f"📚 Retrieved comprehensive context ({len(context)} characters)")
        
        # Use book knowledge if available
        book_knowledge = self.analysis_summary if use_book_knowledge else ""
        if book_knowledge:
            print(f"🧠 Using comprehensive book knowledge ({len(book_knowledge)} characters)")
        
        print(f"🤖 Generating response with {self.model}...")
        
        # Add grace period
        if self.question_final_grace_ms > 0:
            time.sleep(self.question_final_grace_ms / 1000.0)
        
        # Generate response
        answer = self.generate_response(question, context, book_knowledge)
        
        return {
            'answer': answer,
            'chunks_used': n_results,
            'context': context,
            'book_knowledge_used': bool(book_knowledge),
            'model_used': self.model,
            'context_length': len(context),
            'book_knowledge_length': len(book_knowledge) if book_knowledge else 0
        }

def main():
    """Interactive CLI for Enhanced RAG"""
    print("🚀 Initializing Enhanced RAG with Book Analysis...")
    
    # Check for OpenRouter API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set!")
        return
    
    try:
        # Initialize Enhanced RAG
        rag = EnhancedRAG()
        
        # Initialize book knowledge
        rag.initialize_book_knowledge()
        
        print("🎯 Enhanced RAG Ready!")
        print("Ask questions about 'Sidetrack Key' with full book context.")
        print("Type 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                question = input("❓ Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("\n" + "="*60)
                
                # Query the Enhanced RAG
                result = rag.query(question, n_results=20, use_book_knowledge=True)
                
                # Display results
                print(f"💡 Answer:\n{result['answer']}\n")
                
                print(f"📊 Context: {result['context_length']} chars, Book Knowledge: {result['book_knowledge_length']} chars")
                print(f"🤖 Model: {result['model_used']}")
                print(f"🧠 Book Knowledge Used: {result['book_knowledge_used']}")
                
                print("="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    except Exception as e:
        print(f"❌ Failed to initialize Enhanced RAG: {e}")

if __name__ == "__main__":
    main()
