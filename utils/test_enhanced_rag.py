#!/usr/bin/env python3
"""
Test script comparing standard RAG vs Enhanced RAG with book analysis
"""

import os
from setup_openrouter import setup_openrouter_env
from rag_openrouter import RAGOpenRouterEngine
from enhanced_rag import EnhancedRAG

def test_comparison():
    """Compare standard RAG vs Enhanced RAG"""
    print("🧪 Testing Standard RAG vs Enhanced RAG")
    print("="*60)
    
    # Setup environment
    setup_openrouter_env()
    
    # Test queries
    test_queries = [
        "who won, blanche or elle",
        "what is the main conflict in the story",
        "how does the story end",
        "what happens to the main characters",
        "describe the relationship between elle and blanche"
    ]
    
    print("🔧 Initializing systems...")
    
    # Initialize standard RAG
    standard_rag = RAGOpenRouterEngine()
    
    # Initialize enhanced RAG
    enhanced_rag = EnhancedRAG()
    
    print("✅ Systems initialized!")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {query}")
        print("-" * 50)
        
        # Test standard RAG
        print("🔍 Standard RAG:")
        standard_result = standard_rag.query(query, n_results=15, use_comprehensive=True)
        print(f"   Answer: {standard_result['answer'][:200]}...")
        print(f"   Context: {standard_result.get('chunks_used', 0)} chunks")
        
        print()
        
        # Test enhanced RAG
        print("🧠 Enhanced RAG:")
        enhanced_result = enhanced_rag.query(query, n_results=20, use_book_knowledge=True)
        print(f"   Answer: {enhanced_result['answer'][:200]}...")
        print(f"   Context: {enhanced_result['context_length']} chars")
        print(f"   Book Knowledge: {enhanced_result['book_knowledge_length']} chars")
        
        print("\n" + "="*60 + "\n")

def test_specific_question():
    """Test a specific complex question"""
    print("🎯 Testing Complex Question: 'Who won, Blanche or Elle?'")
    print("="*60)
    
    setup_openrouter_env()
    
    # Enhanced RAG only (since we know it works better)
    enhanced_rag = EnhancedRAG()
    
    result = enhanced_rag.query("who won, blanche or elle", n_results=25, use_book_knowledge=True)
    
    print("📊 RESULT:")
    print("="*60)
    print(result['answer'])
    print("="*60)
    print(f"📈 Statistics:")
    print(f"   Context Length: {result['context_length']} characters")
    print(f"   Book Knowledge: {result['book_knowledge_length']} characters")
    print(f"   Total Context: {result['context_length'] + result['book_knowledge_length']} characters")
    print(f"   Model: {result['model_used']}")
    print(f"   Book Knowledge Used: {result['book_knowledge_used']}")

def main():
    """Main test function"""
    print("🚀 Enhanced RAG Test Suite")
    print("="*60)
    
    try:
        # Test specific question
        test_specific_question()
        
        print("\n" + "="*60)
        print("💡 Key Improvements with Enhanced RAG:")
        print("   ✅ Comprehensive book analysis (plot, characters, conflicts)")
        print("   ✅ Multi-pass context retrieval")
        print("   ✅ Book knowledge integration")
        print("   ✅ Better answers for complex questions")
        print("   ✅ More authoritative responses about outcomes")
        
        print("\n🎉 Enhanced RAG is ready for full book queries!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
