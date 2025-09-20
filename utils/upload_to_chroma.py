#!/usr/bin/env python3
"""
Script to upload data from the data directory to ChromaDB Cloud
"""

import os
import chromadb
from pathlib import Path
import hashlib
from typing import List, Dict, Any
import re

class ChromaUploader:
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
                    para_end = text.rfind('\n\n', start, end)
                    if para_end > start + chunk_size - 200:
                        end = para_end + 2
                    else:
                        # Look for word boundaries
                        word_end = text.rfind(' ', start, end)
                        if word_end > start + chunk_size - 50:
                            end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
                
        return chunks
    
    def process_text_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a text file and return chunks with metadata
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of dictionaries containing chunk data and metadata
        """
        print(f"Processing file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean up the text
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Remove excessive newlines
        content = content.strip()
        
        # Chunk the text
        chunks = self.chunk_text(content)
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}_{i}"
            
            documents.append({
                'id': doc_id,
                'text': chunk,
                'metadata': {
                    'source_file': file_path.name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_type': 'text'
                }
            })
        
        print(f"Created {len(documents)} chunks from {file_path.name}")
        return documents
    
    def upload_documents(self, collection_name: str, documents: List[Dict[str, Any]]):
        """
        Upload documents to ChromaDB collection
        
        Args:
            collection_name: Name of the collection
            documents: List of document dictionaries
        """
        try:
            # Get or create collection
            try:
                collection = self.client.get_collection(collection_name)
                print(f"Using existing collection: {collection_name}")
            except:
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Uploaded documents from data directory"}
                )
                print(f"Created new collection: {collection_name}")
            
            # Prepare data for upload
            ids = [doc['id'] for doc in documents]
            texts = [doc['text'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            
            # Upload in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                
                print(f"Uploaded batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
            
            print(f"Successfully uploaded {len(documents)} documents to collection '{collection_name}'")
            
        except Exception as e:
            print(f"Error uploading documents: {e}")
            raise
    
    def upload_data_directory(self, data_dir: str = "data", collection_name: str = "bunny_documents"):
        """
        Upload all files from the data directory to ChromaDB
        
        Args:
            data_dir: Path to the data directory
            collection_name: Name of the ChromaDB collection
        """
        data_path = Path(data_dir)
        
        if not data_path.exists():
            print(f"Data directory '{data_dir}' not found!")
            return
        
        all_documents = []
        
        # Process all text files in the data directory
        for file_path in data_path.glob("*.txt"):
            if file_path.is_file():
                try:
                    documents = self.process_text_file(file_path)
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
        
        if not all_documents:
            print("No documents found to upload!")
            return
        
        print(f"Total documents to upload: {len(all_documents)}")
        
        # Upload all documents
        self.upload_documents(collection_name, all_documents)
        
        # Test the upload
        self.test_collection(collection_name)
    
    def test_collection(self, collection_name: str):
        """
        Test the uploaded collection by performing a sample query
        
        Args:
            collection_name: Name of the collection to test
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Get collection info
            count = collection.count()
            print(f"\nCollection '{collection_name}' contains {count} documents")
            
            # Perform a sample query
            print("\nPerforming sample query...")
            results = collection.query(
                query_texts=["Sidetrack Key"],
                n_results=3
            )
            
            if results['documents'] and results['documents'][0]:
                print("Sample results:")
                for i, doc in enumerate(results['documents'][0][:2]):
                    print(f"\nResult {i+1}:")
                    print(f"Text: {doc[:200]}...")
                    if results['metadatas'] and results['metadatas'][0]:
                        print(f"Metadata: {results['metadatas'][0][i]}")
            else:
                print("No results found for sample query")
                
        except Exception as e:
            print(f"Error testing collection: {e}")

def main():
    """Main function to run the upload process"""
    print("Starting ChromaDB upload process...")
    
    uploader = ChromaUploader()
    uploader.upload_data_directory()
    
    print("\nUpload process completed!")

if __name__ == "__main__":
    main()
