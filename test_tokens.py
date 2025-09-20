#!/usr/bin/env python3

import os
from multi_book_rag import MultiBookRAG

# Test the max tokens setting
print("Testing max tokens configuration...")

# Load environment variables
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# Create RAG instance
rag = MultiBookRAG()

print(f"Max tokens configured: {rag.max_tokens}")
print(f"Model: {rag.model}")

# Test a simple query
try:
    result = rag.query("What is this book about?", book_ids=["nonamekey"], n_results=5)
    if result['success']:
        answer_length = len(result['answer'])
        print(f"Response length: {answer_length} characters")
        print(f"Response preview: {result['answer'][:200]}...")
        
        if answer_length < 1000:
            print("⚠️  WARNING: Response seems short, may be truncated")
        else:
            print("✅ Response appears to be complete")
    else:
        print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error: {e}")
