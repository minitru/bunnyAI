# Multi-Book Enhanced RAG API Examples

## API Endpoints

### Base URL
```
http://localhost:7777
```

## Examples

### 1. Get API Information
```bash
curl http://localhost:7777/
```

### 2. Get System Status
```bash
curl http://localhost:7777/status
```

### 3. Get Available Books
```bash
curl http://localhost:7777/books
```

### 4. Query All Books
```bash
curl -X POST http://localhost:7777/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who are the main characters in these books?"
  }'
```

### 5. Query Specific Book
```bash
curl -X POST http://localhost:7777/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main conflict in Sidetrack Key?",
    "book": "sidetrackkey"
  }'
```

### 6. Query with Custom Context
```bash
curl -X POST http://localhost:7777/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare the themes in both books",
    "context_chunks": 120,
    "use_book_knowledge": true
  }'
```

## Python Client Example

```python
import requests

# Query all books
response = requests.post('http://localhost:7777/query', json={
    'question': 'Who won, blanche or elle?'
})

if response.status_code == 200:
    data = response.json()
    if data['success']:
        print("Answer:", data['answer'])
        print("Books searched:", data['books_searched'])
        print("Processing time:", data['processing_time'], "seconds")
    else:
        print("Error:", data['error'])
else:
    print("HTTP Error:", response.status_code)
```

## JavaScript Client Example

```javascript
// Query specific book
fetch('http://localhost:7777/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        question: 'What is the main character like?',
        book: 'nonamekey'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Answer:', data.answer);
        console.log('Books searched:', data.books_searched);
    } else {
        console.error('Error:', data.error);
    }
});
```

## Request Parameters

### POST /query

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | string | Yes | - | Your question about the books |
| `book` | string | No | null | Book ID to query (defaults to all books) |
| `context_chunks` | integer | No | 80 | Number of context chunks to retrieve |
| `use_book_knowledge` | boolean | No | true | Whether to use comprehensive book knowledge |

### Available Book IDs
- `sidetrackkey` - Sidetrack Key
- `nonamekey` - No Name Key

## Response Format

```json
{
  "success": true,
  "answer": "Detailed literary analysis...",
  "books_searched": ["Sidetrack Key", "No Name Key"],
  "context_length": 40000,
  "processing_time": 2.5
}
```

## Error Response

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```
