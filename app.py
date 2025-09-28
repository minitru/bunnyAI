#!/usr/bin/env python3
"""
Multi-Book Enhanced RAG API
A clean REST API for literary analysis queries
"""

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import os
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
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
        model = data.get('model', 'openai/gpt-4o-mini')  # Default model
        n_results = data.get('context_chunks', 80)
        use_book_knowledge = data.get('use_book_knowledge', True)
        
        # Convert single book to list format for RAG system
        book_ids = [book_id] if book_id else None
        
        rag = get_rag_instance()
        
        # Record start time
        start_time = time.time()
        
        # Perform query with selected model
        result = rag.query(
            question=question,
            book_ids=book_ids,
            n_results=n_results,
            use_book_knowledge=use_book_knowledge,
            model=model
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'books_searched': result['books_searched'],
            'context_length': result['context_length'],
            'chunks_used': result['chunks_used'],
            'model_used': result['model_used'],
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

def refresh_knowledge_graph_worker(rag, book_id, progress_callback=None):
    """Worker function for knowledge graph refresh with progress updates"""
    try:
        print(f"🔄 Worker: Starting KG refresh for {book_id}")
        
        if progress_callback:
            progress_callback("Starting knowledge graph refresh...")
        
        result = rag.refresh_knowledge_graph(book_id)
        
        if progress_callback:
            progress_callback("Knowledge graph refresh completed!")
        
        print(f"✅ Worker: KG refresh completed for {book_id}")
        return result
    except Exception as e:
        error_msg = f'Worker error: {str(e)}'
        print(f"❌ Worker: Error in KG refresh for {book_id}: {e}")
        import traceback
        traceback.print_exc()
        
        if progress_callback:
            progress_callback(f"Error: {error_msg}")
        
        return {'error': error_msg}

def get_status_file_path(book_id):
    """Get the path for the status file for a given book"""
    return f"cache/refresh_status_{book_id.replace(' ', '_').replace('&', 'and')}.json"

def write_status_file(book_id, status_data):
    """Write status data to file with timestamp"""
    status_file = get_status_file_path(book_id)
    try:
        # Add timestamp to status data
        status_data['timestamp'] = time.time()
        with open(status_file, 'w') as f:
            json.dump(status_data, f)
        print(f"📝 Status written to {status_file}: {status_data}")
    except Exception as e:
        print(f"❌ Error writing status file {status_file}: {e}")

def remove_status_file(book_id):
    """Remove the status file for a given book"""
    status_file = get_status_file_path(book_id)
    try:
        if os.path.exists(status_file):
            os.remove(status_file)
            print(f"🗑️ Removed status file: {status_file}")
    except Exception as e:
        print(f"❌ Error removing status file {status_file}: {e}")

def read_status_file(book_id):
    """Read status file and check if it's stale (older than 20 minutes)"""
    status_file = get_status_file_path(book_id)
    try:
        if not os.path.exists(status_file):
            return None
        
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        # Check if file is older than 20 minutes (1200 seconds)
        current_time = time.time()
        file_timestamp = status_data.get('timestamp', 0)
        age_seconds = current_time - file_timestamp
        
        if age_seconds > 1200:  # 20 minutes
            print(f"⏰ Status file {status_file} is stale ({age_seconds:.0f}s old), removing")
            remove_status_file(book_id)
            return None
        
        return status_data
    except Exception as e:
        print(f"❌ Error reading status file {status_file}: {e}")
        return None

def generate_refresh_stream(book_id):
    """Generate streaming response with keepalive for knowledge graph refresh"""
    def progress_callback(message):
        # Send progress update as Server-Sent Events
        yield f"data: {json.dumps({'type': 'progress', 'message': message})}\n\n"
    
    try:
        print(f"🔄 Starting streaming KG refresh for: {book_id}")
        
        # Validate book_id
        if not book_id or not isinstance(book_id, str):
            yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid book_id provided'})}\n\n"
            return
        
        rag = get_rag_instance()
        print(f"✅ RAG instance obtained for {book_id}")
        
        # Send initial progress
        yield f"data: {json.dumps({'type': 'progress', 'message': 'Initializing knowledge graph refresh...'})}\n\n"
        
        # Start the refresh in a thread with progress updates
        result_container = {'result': None, 'error': None}
        
        def refresh_worker():
            try:
                print(f"🔄 Worker thread starting for {book_id}")
                result = rag.refresh_knowledge_graph(book_id)
                print(f"✅ Worker thread completed for {book_id}, result type: {type(result)}")
                result_container['result'] = result
                print(f"✅ Result container set for {book_id}")
            except Exception as e:
                print(f"❌ Error in refresh worker for {book_id}: {e}")
                import traceback
                traceback.print_exc()
                result_container['error'] = str(e)
        
        # Start the worker thread
        worker_thread = threading.Thread(target=refresh_worker)
        worker_thread.daemon = True  # Make it a daemon thread
        worker_thread.start()
        
        # Send heartbeat every 10 seconds while waiting
        start_time = time.time()
        last_heartbeat = start_time
        max_wait_time = 600  # 10 minutes max
        
        while worker_thread.is_alive() and (time.time() - start_time) < max_wait_time:
            current_time = time.time()
            
            # Send heartbeat every 10 seconds
            if current_time - last_heartbeat >= 10:
                elapsed = int(current_time - start_time)
                yield f"data: {json.dumps({'type': 'heartbeat', 'message': f'Processing... ({elapsed}s elapsed)', 'elapsed': elapsed})}\n\n"
                last_heartbeat = current_time
            
            time.sleep(1)  # Check every second
        
        # Check if we timed out
        if worker_thread.is_alive():
            print(f"⏰ Thread still alive after {max_wait_time}s, forcing timeout")
            yield f"data: {json.dumps({'type': 'error', 'error': f'Knowledge graph refresh timed out after {max_wait_time} seconds'})}\n\n"
            return
        
        # Wait for thread to complete
        worker_thread.join(timeout=5)  # 5 second timeout for join
        
        print(f"🔍 Thread completed for {book_id}. Result: {type(result_container['result'])}, Error: {result_container['error']}")
        
        # Check result
        if result_container['error']:
            print(f"❌ Sending error response for {book_id}: {result_container['error']}")
            yield f"data: {json.dumps({'type': 'error', 'error': result_container['error']})}\n\n"
        elif result_container['result']:
            # Check if the result is an error dictionary
            if isinstance(result_container['result'], dict) and 'error' in result_container['result']:
                print(f"❌ Sending error response for {book_id}: {result_container['result']['error']}")
                yield f"data: {json.dumps({'type': 'error', 'error': result_container['result']['error']})}\n\n"
            else:
                # Success - send a simple success message
                print(f"✅ Sending success response for {book_id}")
                success_msg = json.dumps({'type': 'success', 'message': 'Knowledge graph refresh completed successfully'})
                print(f"✅ Success message: {success_msg}")
                yield f"data: {success_msg}\n\n"
                print(f"✅ Success message yielded for {book_id}")
                # Ensure the stream is properly closed
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        else:
            print(f"❌ No result for {book_id}")
            yield f"data: {json.dumps({'type': 'error', 'error': 'No result returned from refresh operation'})}\n\n"
            
    except Exception as e:
        print(f"❌ Exception in streaming refresh for {book_id}: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'error': f'Failed to refresh knowledge graph: {str(e)}'})}\n\n"

@app.route('/api/knowledge-graph/<book_id>/status', methods=['GET'])
def get_refresh_status(book_id):
    """Get the current refresh status for a book"""
    status_data = read_status_file(book_id)
    if status_data:
        # Add elapsed time to the status data
        current_time = time.time()
        file_timestamp = status_data.get('timestamp', current_time)
        elapsed = int(current_time - file_timestamp)
        status_data['elapsed'] = elapsed
        
        # Return the status file contents with elapsed time
        return jsonify(status_data)
    else:
        return jsonify({
            'status': 'idle',
            'message': 'No refresh in progress'
        })

@app.route('/api/test-sse', methods=['GET'])
def test_sse():
    """Test endpoint for EventSource"""
    def generate_test_stream():
        yield f"data: {json.dumps({'type': 'test', 'message': 'Test message 1'})}\n\n"
        import time
        time.sleep(2)
        yield f"data: {json.dumps({'type': 'test', 'message': 'Test message 2'})}\n\n"
        time.sleep(2)
        yield f"data: {json.dumps({'type': 'test', 'message': 'Test message 3'})}\n\n"
    
    return Response(
        generate_test_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/knowledge-graph/<book_id>/refresh', methods=['GET'])
def refresh_knowledge_graph_file_based(book_id):
    """Start knowledge graph refresh using file-based status tracking"""
    print(f"🔄 Starting file-based knowledge graph refresh for: {book_id}")
    
    # Clean up any old status files first
    remove_status_file(book_id)
    print(f"🧹 Cleaned up any old status files for {book_id}")
    
    # Check if refresh is already in progress (should be none after cleanup)
    existing_status = read_status_file(book_id)
    if existing_status:
        return jsonify({
            'status': 'already_running',
            'message': 'Refresh already in progress',
            'elapsed': int(time.time() - existing_status.get('timestamp', time.time()))
        })
    
    # Validate book_id
    if not book_id or not isinstance(book_id, str):
        return jsonify({'error': 'Invalid book_id provided'}), 400
    
    # Start the refresh in a background thread
    def refresh_worker():
        try:
            print(f"🔄 Background refresh worker starting for: {book_id}")
            
            # Write initial status
            write_status_file(book_id, {
                'status': 'starting',
                'message': 'Initializing knowledge graph refresh...',
                'progress': 0
            })
            
            rag = get_rag_instance()
            print(f"✅ RAG instance obtained for {book_id}")
            
            # Update status
            write_status_file(book_id, {
                'status': 'processing',
                'message': 'Extracting entities and relationships...',
                'progress': 25
            })
            
            # Perform the refresh
            result = rag.refresh_knowledge_graph(book_id)
            
            # Check result
            if isinstance(result, dict) and 'error' in result:
                write_status_file(book_id, {
                    'status': 'error',
                    'message': f"Error: {result['error']}",
                    'progress': 100
                })
                print(f"❌ Refresh failed for {book_id}: {result['error']}")
            else:
                write_status_file(book_id, {
                    'status': 'completed',
                    'message': 'Knowledge graph refresh completed successfully!',
                    'progress': 100
                })
                print(f"✅ Refresh completed for {book_id}")
            
            # Remove status file after a short delay to allow frontend to read final status
            time.sleep(2)
            remove_status_file(book_id)
            
        except Exception as e:
            print(f"❌ Error in refresh worker for {book_id}: {e}")
            import traceback
            traceback.print_exc()
            write_status_file(book_id, {
                'status': 'error',
                'message': f"Error: {str(e)}",
                'progress': 100
            })
            time.sleep(2)
            remove_status_file(book_id)
    
    # Start the worker thread
    worker_thread = threading.Thread(target=refresh_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Knowledge graph refresh started in background'
    })

@app.route('/api/knowledge-graph/<book_id>/refresh', methods=['POST'])
def refresh_knowledge_graph(book_id):
    """Force refresh the knowledge graph (POST for backward compatibility)"""
    print(f"🔄 Starting knowledge graph refresh for: {book_id}")
    
    # For POST requests, redirect to the streaming endpoint
    return jsonify({
        'success': True,
        'message': 'Please use GET request for streaming refresh, or use the web interface',
        'streaming_url': f'/api/knowledge-graph/{book_id}/refresh'
    })



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
