#!/usr/bin/env python3
"""
Multi-Book Enhanced RAG API
A clean REST API for literary analysis queries
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import time
from dotenv import load_dotenv
from multi_book_rag import MultiBookRAG

app = Flask(__name__)
CORS(app)

# Global RAG instance
rag_instance = None

def get_rag_instance():
    """Get or create the RAG instance"""
    global rag_instance
    if rag_instance is None:
        load_dotenv()
        rag_instance = MultiBookRAG()
        rag_instance.initialize_book_knowledge()
    return rag_instance

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'Multi-Book Enhanced RAG API',
        'version': '1.0.0',
        'description': 'Literary analysis API for querying multiple books',
        'endpoints': {
            'GET /': 'Web interface',
            'GET /api': 'API information',
            'GET /api/books': 'Get available books',
            'POST /api/query': 'Query books for literary analysis',
            'GET /api/status': 'Get system status'
        }
    })

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get available books"""
    try:
        rag = get_rag_instance()
        books = rag.get_available_books()
        return jsonify({
            'success': True,
            'books': books
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query', methods=['POST'])
def query_books():
    """
    Query the RAG system for literary analysis
    
    Request body:
    {
        "question": "Your question about the books",
        "book": "optional book_id (defaults to all books)",
        "context_chunks": 80,  # optional, defaults to 80
        "use_book_knowledge": true  # optional, defaults to true
    }
    
    Response:
    {
        "success": true,
        "answer": "Detailed literary analysis...",
        "books_searched": ["Book Title 1", "Book Title 2"],
        "context_length": 40000,
        "processing_time": 2.5
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
            
        question = data.get('question', '').strip()
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        # Optional parameters with defaults
        book_id = data.get('book', None)  # None means all books
        n_results = data.get('context_chunks', 80)
        use_book_knowledge = data.get('use_book_knowledge', True)
        
        # Convert single book to list format for RAG system
        book_ids = [book_id] if book_id else None
        
        rag = get_rag_instance()
        
        # Record start time
        start_time = time.time()
        
        # Perform query
        result = rag.query(
            question=question,
            book_ids=book_ids,
            n_results=n_results,
            use_book_knowledge=use_book_knowledge
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'books_searched': result['books_searched'],
            'context_length': result['context_length'],
            'chunks_used': result['chunks_used'],
            'processing_time': round(processing_time, 2)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        rag = get_rag_instance()
        books = rag.get_available_books()
        return jsonify({
            'success': True,
            'books_loaded': len(books),
            'total_chunks': sum(book['chunk_count'] for book in books),
            'system_ready': True,
            'available_books': [book['book_title'] for book in books],
            'conversation_history_length': len(rag.conversation_history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'system_ready': False
        }), 500

@app.route('/api/clear-memory', methods=['POST'])
def clear_conversation_memory():
    """Clear conversation history"""
    try:
        rag = get_rag_instance()
        rag.clear_conversation_history()
        return jsonify({
            'success': True,
            'message': 'Conversation history cleared'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Multi-Book RAG Web Application...")
    print("📚 Initializing system...")
    
    # Initialize the RAG system
    try:
        get_rag_instance()
        print("✅ System initialized successfully!")
        print("🌐 Starting web server on all interfaces (0.0.0.0:7777)")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=7777)
