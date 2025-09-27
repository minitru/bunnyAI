# a Multi-Book Enhanced RAG API - Literary Analysis

A sophisticated REST API for deep literary analysis of multiple books using ChromaDB and Claude 3.5 Sonnet. Query books individually or together with comprehensive context and professional literary analysis.

## 🚀 Quick Start

### Start the API Server
```bash
# 1. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start the API server
python app.py

# 4. API will be available at http://localhost:7777
```

### Test the API
```bash
# Test with curl
curl -X POST http://localhost:7777/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the main characters?"}'

# Or use the Python client
python api_client.py
```

### Command Line Interface (Alternative)
```bash
# 1. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the multi-book system
python main_multi_book.py
```

## 📁 System Architecture

### Core Files
- **`app.py`** - REST API server (Flask)
- **`api_client.py`** - Python client example
- **`api_examples.md`** - API usage examples and documentation
- **`main_multi_book.py`** - Command-line interface for multi-book system
- **`multi_book_rag.py`** - Multi-book RAG system with comprehensive context
- **`multi_book_analyzer.py`** - Multi-book analysis with caching
- **`test_web.py`** - Web API test suite

### Utils Directory (`utils/`)
- **`upload_multi_book.py`** - Multi-book data upload script
- **`cost_calculator.py`** - Query cost calculation tool
- **`change_model.py`** - Quick model switcher

## 🎯 Features

### REST API
- **Clean, simple endpoints** for easy integration
- **JSON request/response** format
- **Optional book selection** - query specific books or all books
- **Configurable context** - adjust chunk count and knowledge usage
- **Comprehensive error handling** with detailed error messages

### Multi-Book Support
- **Query one book** or both books together
- **Sidetrack Key** (555 chunks) and **No Name Key** (562 chunks)
- **Comprehensive cross-book analysis** and comparison
- **Book-specific queries** with targeted context

### Enhanced Context Retrieval
- **80 chunks** per query for maximum context
- **40,000+ characters** of context per query
- **Comprehensive book analysis** with 200+ chunks
- **Multi-pass retrieval** with character and conflict detection

### Advanced Book Analysis
- **Complete book summary** with 10 detailed sections
- **Character analysis** with psychological depth
- **Plot and conflict analysis** with story structure
- **Caching system** for fast subsequent queries

### Literary Editor Persona
- **30 years of experience** literary editor
- **Deep, insightful analysis** with practical suggestions
- **Respectful of author's voice** while providing constructive feedback

## 🔧 Configuration

### Environment Setup
The system uses a `.env` file for secure configuration. Copy `.env.example` to `.env` and fill in your API keys:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual API keys
nano .env
```

### Required Environment Variables
```bash
# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_MAX_TOKENS=8000
OPENROUTER_TEMPERATURE=0.3
OPENROUTER_FORCE_JSON=0
QUESTION_FINAL_GRACE_MS=1200
TOKENIZERS_PARALLELISM=false

# ChromaDB Configuration
CHROMADB_API_KEY=your_chromadb_api_key_here
CHROMADB_TENANT=your_chromadb_tenant_here
CHROMADB_DATABASE=your_chromadb_database_here
```

### Current Model: Claude 3.5 Sonnet
- **Provider**: Anthropic
- **Context**: 200k tokens
- **Quality**: 8/10 for literary analysis
- **Cost**: Medium

## 📊 Performance

### Context Enhancement
- **Before**: ~13,000 characters
- **After**: ~41,000 characters (3x improvement)
- **Book Analysis**: 100+ chunks vs 50 before
- **Character Queries**: 15+ specific searches
- **Plot Queries**: 20+ conflict-related searches

### Caching
- **First run**: ~2-3 minutes (full analysis)
- **Subsequent runs**: ~15 seconds (cached)
- **Cache expiry**: 7 days
- **Cache validation**: Content hash-based

## 🎮 Usage Examples

### API Usage
```bash
# Query all books
curl -X POST http://localhost:7777/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the main characters?"}'

# Query specific book
curl -X POST http://localhost:7777/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main conflict?", "book": "sidetrackkey"}'
```

### Python Client
```python
from api_client import LiteraryAnalysisAPI

api = LiteraryAnalysisAPI()
result = api.query("Who won, blanche or elle?", book="sidetrackkey")
print(result['answer'])
```

### Command Line Interface
```bash
python main_multi_book.py
```

### Programmatic Usage
```python
from dotenv import load_dotenv
from multi_book_rag import MultiBookRAG

load_dotenv()
rag = MultiBookRAG()
rag.initialize_book_knowledge()

# Query all books
result = rag.query("who are the main characters in both books?", n_results=80)

# Query specific book
result = rag.query("who won, blanche or elle?", book_ids=['sidetrackkey'], n_results=80)
print(result['answer'])
```

### Utility Tools
```bash
# Cost calculation
python utils/cost_calculator.py

# Model selection
python utils/change_model.py

# Upload books
python utils/upload_multi_book.py

# Test web API
python test_web.py
```

## 🧹 Cleanup

All old/outdated RAG system files have been removed:
- ❌ `rag_openrouter.py` (old version)
- ❌ `rag_query_engine.py` (old version)
- ❌ `demo_rag.py` (old version)
- ❌ `test_rag.py` (old version)
- ❌ `test_openrouter.py` (old version)
- ❌ `engine_comparison.py` (old version)
- ❌ `utils/enhanced_rag.py` (single-book system)
- ❌ `utils/book_analyzer.py` (single-book analyzer)
- ❌ `utils/upload_to_chroma.py` (legacy upload script)
- ❌ `utils/test_enhanced_rag.py` (broken test file)
- ❌ `utils/test_caching.py` (broken test file)
- ❌ `utils/cache_manager.py` (single-book cache manager)
- ❌ `utils/model_selector.py` (single-book model selector)
- ❌ `utils/component_analysis.md` (outdated documentation)
- ❌ `setup_openrouter.py` (replaced with direct .env loading)
- ❌ `test_tokens.py` (outdated test script)
- ❌ `bunny-ai-plugin.php` (WordPress plugin)
- ❌ `wordpress-shortcode.php` (WordPress shortcode)
- ❌ `WORDPRESS_INTEGRATION.md` (WordPress documentation)

## 📈 System Status

✅ **REST API** (Flask, clean endpoints, JSON format)  
✅ **Multi-book support** (Sidetrack Key + No Name Key + Wanda & Me - Act 1)  
✅ **Enhanced context retrieval** (80 chunks, 40k+ chars)  
✅ **Comprehensive book analysis** (200+ chunks, 10 sections)  
✅ **Claude 3.5 Sonnet** (best for literary analysis)  
✅ **Caching system** (7-day expiry, hash validation)  
✅ **Literary editor persona** (30 years experience)  
✅ **Secure configuration** (.env file, API keys protected)  
✅ **Clean architecture** (utils organized, old files removed)  

The system now provides a clean REST API that can be easily integrated into other applications, along with command-line access for deep, comprehensive literary analysis across multiple books with maximum context and the best available model for the task.
