#!/usr/bin/env python3
"""
Main Entry Point for Multi-Book Enhanced RAG System
"""

import os
import sys
from setup_openrouter import setup_openrouter_env
from multi_book_rag import MultiBookRAG

def main():
    """Main interactive interface for the Multi-Book Enhanced RAG system"""
    print("🎯 Multi-Book Enhanced RAG System - Literary Analysis")
    print("="*60)
    
    # Setup environment
    setup_openrouter_env()
    
    # Initialize RAG system
    print("🚀 Initializing Multi-Book Enhanced RAG System...")
    rag = MultiBookRAG()
    
    # Show available books
    books = rag.get_available_books()
    print(f"📚 Available books: {len(books)}")
    for i, book in enumerate(books):
        print(f"   {i+1}. {book['book_title']} ({book['chunk_count']} chunks)")
    
    # Initialize book knowledge
    rag.initialize_book_knowledge()
    
    print("\n✅ System ready! Ask questions about the books")
    print("💡 Examples:")
    print("   'who won, blanche or elle' (Sidetrack Key)")
    print("   'analyze the main character in No Name Key'")
    print("   'compare the themes in both books'")
    print("   'help' for more options")
    
    while True:
        try:
            question = input("\n📚 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif question.lower() == 'help':
                show_help(books)
                continue
            elif question.lower() == 'books':
                show_books(books)
                continue
            elif question.lower().startswith('book '):
                # Handle book-specific queries
                book_num = question.lower().replace('book ', '').strip()
                if book_num.isdigit():
                    book_idx = int(book_num) - 1
                    if 0 <= book_idx < len(books):
                        book_id = books[book_idx]['book_id']
                        specific_question = input(f"📖 Question about {books[book_idx]['book_title']}: ").strip()
                        if specific_question:
                            print(f"\n🔍 Analyzing {books[book_idx]['book_title']}...")
                            result = rag.query(specific_question, book_ids=[book_id], n_results=80, use_book_knowledge=True)
                            display_result(result, books[book_idx]['book_title'])
                        continue
                    else:
                        print(f"❌ Invalid book number. Please choose 1-{len(books)}")
                        continue
            elif not question:
                continue
            
            print("\n🔍 Analyzing...")
            result = rag.query(question, n_results=80, use_book_knowledge=True)
            display_result(result, "All Books")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'help' for assistance.")

def show_help(books):
    """Show help information"""
    print("\n📋 HELP - Available Commands:")
    print("="*40)
    print("• Ask any question about the books")
    print("• 'book 1' - Ask question about first book")
    print("• 'book 2' - Ask question about second book")
    print("• 'books' - Show available books")
    print("• 'help' - Show this help")
    print("• 'quit' - Exit the system")
    print("\n💡 Question Examples:")
    print("• 'who won, blanche or elle'")
    print("• 'analyze the character development of Elle'")
    print("• 'what are the main conflicts in both books'")
    print("• 'compare the themes in Sidetrack Key and No Name Key'")
    print("• 'explain the symbolism in the books'")
    print("• 'how does the setting affect the story'")

def show_books(books):
    """Show available books"""
    print(f"\n📚 Available books:")
    for i, book in enumerate(books):
        print(f"   {i+1}. {book['book_title']} ({book['chunk_count']} chunks)")
    print(f"\n💡 Use 'book 1' or 'book 2' to ask questions about specific books")

def display_result(result, source):
    """Display query result"""
    print("\n" + "="*60)
    print(f"📖 LITERARY ANALYSIS - {source}")
    print("="*60)
    print(result['answer'])
    print("\n" + "="*60)
    print(f"📊 Context: {result['context_length']:,} chars | Book Knowledge: {result['book_knowledge_length']:,} chars")
    print(f"📚 Books searched: {len(result['books_searched'])}")

if __name__ == "__main__":
    main()
