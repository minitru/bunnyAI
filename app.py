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

@app.route('/force-graph')
def force_graph():
    """Serve the force graph visualization page"""
    return render_template('force_graph.html')

@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'Multi-Book Enhanced RAG API',
        'version': '1.0.0',
        'description': 'Literary analysis API for querying multiple books',
        'endpoints': {
            'GET /': 'Web interface',
            'GET /force-graph': 'Force graph visualization page',
            'GET /api': 'API information',
            'GET /api/books': 'Get available books',
            'POST /api/query': 'Query books for literary analysis',
            'GET /api/status': 'Get system status',
            'GET /api/knowledge-graph/<book_id>': 'Get knowledge graph for a book',
            'POST /api/knowledge-graph/<book_id>/refresh': 'Refresh knowledge graph with improved extraction',
            'GET /api/force-graph/<book_id>': 'Get force graph data for visualization',
            'GET /api/force-graph/combined': 'Get combined force graph for all books',
            'POST /api/entities/search': 'Search entities in knowledge graph',
            'GET /api/entities/<book_id>/<entity_id>/relationships': 'Get entity relationships'
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

@app.route('/api/knowledge-graph/<book_id>', methods=['GET'])
def get_knowledge_graph(book_id):
    """Get knowledge graph for a specific book"""
    try:
        rag = get_rag_instance()
        kg_data = rag.get_knowledge_graph(book_id)
        
        if not kg_data:
            return jsonify({
                'success': False,
                'error': f'No knowledge graph found for book {book_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'knowledge_graph': kg_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/force-graph/<book_id>', methods=['GET'])
def get_force_graph(book_id):
    """Get force graph data for visualization"""
    try:
        rag = get_rag_instance()
        force_graph_data = rag.get_force_graph_data(book_id)
        
        return jsonify({
            'success': True,
            'force_graph': force_graph_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/force-graph/combined', methods=['GET'])
def get_combined_force_graph():
    """Get combined force graph data for all books"""
    try:
        rag = get_rag_instance()
        force_graph_data = rag.get_combined_force_graph_data()
        
        return jsonify({
            'success': True,
            'force_graph': force_graph_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/entities/search', methods=['POST'])
def search_entities():
    """Search for entities in the knowledge graph"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        book_id = data.get('book_id', None)
        limit = data.get('limit', 10)
        
        rag = get_rag_instance()
        entities = rag.search_entities(query, book_id, limit)
        
        return jsonify({
            'success': True,
            'entities': entities,
            'query': query,
            'book_id': book_id,
            'count': len(entities)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/entities/<book_id>/<entity_id>/relationships', methods=['GET'])
def get_entity_relationships(book_id, entity_id):
    """Get all relationships for a specific entity"""
    try:
        rag = get_rag_instance()
        relationships = rag.get_entity_relationships(entity_id, book_id)
        
        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'book_id': book_id,
            'relationships': relationships,
            'count': len(relationships)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/knowledge-graph/<book_id>/refresh', methods=['POST'])
def refresh_knowledge_graph(book_id):
    """Force refresh the knowledge graph with improved extraction"""
    try:
        rag = get_rag_instance()
        kg_data = rag.refresh_knowledge_graph(book_id)
        
        if 'error' in kg_data:
            return jsonify({
                'success': False,
                'error': kg_data['error']
            }), 400
        
        return jsonify({
            'success': True,
            'knowledge_graph': kg_data,
            'message': f'Knowledge graph refreshed for {book_id}'
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
