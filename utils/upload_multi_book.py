#!/usr/bin/env python3
"""
Multi-Book Upload Script for ChromaDB Cloud
Supports uploading multiple books with proper metadata and book identification
"""

import os
import chromadb
from pathlib import Path
import hashlib
from typing import List, Dict, Any, Optional
import re
import json

class MultiBookUploader:
    def __init__(self):
        """Initialize ChromaDB Cloud client"""
        self.client = chromadb.CloudClient(
            api_key=os.getenv('CHROMADB_API_KEY'),
            tenant=os.getenv('CHROMADB_TENANT'),
            database=os.getenv('CHROMADB_DATABASE')
        )
        
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval
        
        Args:
            text: The text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size - 100:
                    end = sentence_end + 1
                else:
                    # Look for paragraph breaks
                    para_break = text.rfind('\n\n', start, end)
                    if para_break > start + chunk_size - 200:
                        end = para_break + 2
                    else:
                        # Look for single line breaks
                        line_break = text.rfind('\n', start, end)
                        if line_break > start + chunk_size - 300:
                            end = line_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def get_book_info(self, file_path: Path) -> Dict[str, str]:
        """
        Extract book information from filename and content
        
        Args:
            file_path: Path to the book file
            
        Returns:
            Dictionary with book information
        """
        filename = file_path.stem.lower()
        
        # Map filenames to book titles
        book_mapping = {
            'sidetrackkey': 'Sidetrack Key',
            'nonamekey': 'No Name Key',
            'sidetrack_key': 'Sidetrack Key',
            'no_name_key': 'No Name Key'
        }
        
        book_title = book_mapping.get(filename, filename.replace('_', ' ').title())
        
        # Read first few lines to get more info
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_lines = f.read(500)
                
            # Try to extract author or other info from content
            author = "Unknown Author"
            if "by " in first_lines.lower():
                author_match = re.search(r'by\s+([^\n]+)', first_lines, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
        except:
            author = "Unknown Author"
        
        return {
            'book_title': book_title,
            'book_id': filename,
            'author': author,
            'filename': file_path.name
        }
    
    def upload_single_book(self, file_path: Path, collection_name: str = "multi_book_documents") -> Dict[str, Any]:
        """
        Upload a single book to ChromaDB
        
        Args:
            file_path: Path to the book file
            collection_name: Name of the ChromaDB collection
            
        Returns:
            Upload statistics
        """
        print(f"📚 Processing book: {file_path.name}")
        
        # Get book information
        book_info = self.get_book_info(file_path)
        print(f"   Title: {book_info['book_title']}")
        print(f"   Author: {book_info['author']}")
        
        # Read the book content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return {'error': str(e)}
        
        print(f"   Content length: {len(content):,} characters")
        
        # Chunk the text
        chunks = self.chunk_text(content)
        print(f"   Created {len(chunks)} chunks")
        
        # Prepare documents for upload
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{book_info['book_id']}_chunk_{i}"
            
            document = {
                'id': doc_id,
                'text': chunk,
                'metadata': {
                    'book_title': book_info['book_title'],
                    'book_id': book_info['book_id'],
                    'author': book_info['author'],
                    'filename': book_info['filename'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunk_size': len(chunk)
                }
            }
            documents.append(document)
        
        # Upload to ChromaDB
        try:
            # Get or create collection
            try:
                collection = self.client.get_collection(collection_name)
                print(f"   Using existing collection: {collection_name}")
            except:
                collection = self.client.create_collection(collection_name)
                print(f"   Created new collection: {collection_name}")
            
            # Upload in batches
            batch_size = 100
            total_uploaded = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Extract data for ChromaDB
                ids = [doc['id'] for doc in batch]
                texts = [doc['text'] for doc in batch]
                metadatas = [doc['metadata'] for doc in batch]
                
                # Check if documents already exist
                existing_ids = collection.get(ids=ids)['ids']
                new_ids = [id for id in ids if id not in existing_ids]
                new_texts = [text for i, text in enumerate(texts) if ids[i] in new_ids]
                new_metadatas = [metadata for i, metadata in enumerate(metadatas) if ids[i] in new_ids]
                
                if new_ids:
                    collection.add(
                        ids=new_ids,
                        documents=new_texts,
                        metadatas=new_metadatas
                    )
                
                total_uploaded += len(batch)
                print(f"   Uploaded batch {i//batch_size + 1}: {total_uploaded}/{len(documents)} chunks")
            
            print(f"✅ Successfully uploaded {book_info['book_title']}")
            
            return {
                'book_title': book_info['book_title'],
                'book_id': book_info['book_id'],
                'chunks_uploaded': len(documents),
                'total_characters': len(content),
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ Error uploading {book_info['book_title']}: {e}")
            return {'error': str(e), 'book_title': book_info['book_title']}
    
    def upload_multiple_books(self, data_dir: str = "data", collection_name: str = "multi_book_documents") -> Dict[str, Any]:
        """
        Upload multiple books from the data directory
        
        Args:
            data_dir: Path to the data directory
            collection_name: Name of the ChromaDB collection
            
        Returns:
            Upload statistics for all books
        """
        data_path = Path(data_dir)
        
        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return {'error': 'Data directory not found'}
        
        # Find all text files
        text_files = list(data_path.glob("*.txt"))
        
        if not text_files:
            print(f"❌ No .txt files found in {data_dir}")
            return {'error': 'No text files found'}
        
        print(f"📚 Found {len(text_files)} books to upload:")
        for file_path in text_files:
            print(f"   - {file_path.name}")
        print()
        
        # Upload each book
        results = []
        total_chunks = 0
        total_characters = 0
        
        for file_path in text_files:
            result = self.upload_single_book(file_path, collection_name)
            results.append(result)
            
            if 'chunks_uploaded' in result:
                total_chunks += result['chunks_uploaded']
                total_characters += result['total_characters']
            print()
        
        # Summary
        successful_books = [r for r in results if 'status' in r and r['status'] == 'success']
        failed_books = [r for r in results if 'error' in r]
        
        print("📊 UPLOAD SUMMARY:")
        print("=" * 50)
        print(f"✅ Successful uploads: {len(successful_books)}")
        print(f"❌ Failed uploads: {len(failed_books)}")
        print(f"📚 Total chunks uploaded: {total_chunks:,}")
        print(f"📝 Total characters: {total_characters:,}")
        print()
        
        if successful_books:
            print("📖 Successfully uploaded books:")
            for result in successful_books:
                print(f"   - {result['book_title']} ({result['chunks_uploaded']} chunks)")
        
        if failed_books:
            print("❌ Failed uploads:")
            for result in failed_books:
                print(f"   - {result.get('book_title', 'Unknown')}: {result['error']}")
        
        return {
            'successful_books': len(successful_books),
            'failed_books': len(failed_books),
            'total_chunks': total_chunks,
            'total_characters': total_characters,
            'results': results
        }
    
    def list_books_in_collection(self, collection_name: str = "multi_book_documents") -> List[Dict[str, Any]]:
        """
        List all books in a collection
        
        Args:
            collection_name: Name of the ChromaDB collection
            
        Returns:
            List of book information
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Get all documents to extract unique books
            all_docs = collection.get()
            
            if not all_docs['documents']:
                return []
            
            # Group by book_id
            books = {}
            for i, metadata in enumerate(all_docs['metadatas']):
                book_id = metadata.get('book_id', 'unknown')
                if book_id not in books:
                    books[book_id] = {
                        'book_id': book_id,
                        'book_title': metadata.get('book_title', 'Unknown'),
                        'author': metadata.get('author', 'Unknown'),
                        'filename': metadata.get('filename', 'Unknown'),
                        'chunk_count': 0,
                        'total_chunks': metadata.get('total_chunks', 0)
                    }
                books[book_id]['chunk_count'] += 1
            
            return list(books.values())
            
        except Exception as e:
            print(f"❌ Error listing books: {e}")
            return []

def main():
    """Main function to upload multiple books"""
    print("🚀 Multi-Book Upload to ChromaDB Cloud")
    print("=" * 50)
    
    uploader = MultiBookUploader()
    
    # Upload all books
    result = uploader.upload_multiple_books()
    
    if 'error' not in result:
        print("\n📋 Books in collection:")
        books = uploader.list_books_in_collection()
        for book in books:
            print(f"   - {book['book_title']} by {book['author']} ({book['chunk_count']} chunks)")
    
    print("\n✅ Upload process complete!")

if __name__ == "__main__":
    main()
