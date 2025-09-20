// Multi-Book Literary Analysis Frontend JavaScript

class LiteraryAnalysisApp {
    constructor() {
        this.selectedBooks = [];
        this.books = [];
        this.init();
    }

    async init() {
        await this.loadBooks();
        await this.loadSystemStatus();
        this.setupEventListeners();
    }

    async loadBooks() {
        try {
            const response = await fetch('/api/books');
            const data = await response.json();
            
            if (data.success) {
                this.books = data.books;
                this.renderBooks();
                this.updateStatusIndicator('ready');
            } else {
                this.showError('Failed to load books: ' + data.error);
                this.updateStatusIndicator('error');
            }
        } catch (error) {
            this.showError('Failed to connect to server: ' + error.message);
            this.updateStatusIndicator('error');
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.renderSystemStatus(data.status);
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }

    renderBooks() {
        const booksList = document.getElementById('books-list');
        
        if (this.books.length === 0) {
            booksList.innerHTML = '<p class="text-muted">No books available</p>';
            return;
        }

        booksList.innerHTML = this.books.map(book => `
            <div class="book-item" data-book-id="${book.book_id}" onclick="app.toggleBookSelection('${book.book_id}')">
                <div class="book-title">${book.book_title}</div>
                <div class="book-meta">
                    <i class="fas fa-file-alt me-1"></i>
                    ${book.chunk_count} chunks
                    <br>
                    <i class="fas fa-user me-1"></i>
                    ${book.author}
                </div>
            </div>
        `).join('');

        // Add "All Books" option
        booksList.innerHTML = `
            <div class="book-item selected" data-book-id="all" onclick="app.toggleBookSelection('all')">
                <div class="book-title">
                    <i class="fas fa-books me-2"></i>
                    All Books
                </div>
                <div class="book-meta">
                    <i class="fas fa-chart-bar me-1"></i>
                    ${this.books.reduce((sum, book) => sum + book.chunk_count, 0)} total chunks
                </div>
            </div>
        ` + booksList.innerHTML;

        // Select "All Books" by default
        this.selectedBooks = [];
    }

    renderSystemStatus(status) {
        const statusDiv = document.getElementById('system-status');
        statusDiv.innerHTML = `
            <div class="row text-center">
                <div class="col-6">
                    <div class="h5 text-primary">${status.books_loaded}</div>
                    <div class="small text-muted">Books Loaded</div>
                </div>
                <div class="col-6">
                    <div class="h5 text-success">${status.total_chunks.toLocaleString()}</div>
                    <div class="small text-muted">Total Chunks</div>
                </div>
            </div>
            <div class="mt-2 text-center">
                <span class="badge bg-success">
                    <i class="fas fa-check-circle me-1"></i>
                    System Ready
                </span>
            </div>
        `;
    }

    toggleBookSelection(bookId) {
        const bookItem = document.querySelector(`[data-book-id="${bookId}"]`);
        
        if (bookId === 'all') {
            // Select all books
            this.selectedBooks = [];
            document.querySelectorAll('.book-item').forEach(item => {
                item.classList.remove('selected');
            });
            bookItem.classList.add('selected');
        } else {
            // Toggle individual book
            if (this.selectedBooks.includes(bookId)) {
                this.selectedBooks = this.selectedBooks.filter(id => id !== bookId);
                bookItem.classList.remove('selected');
            } else {
                this.selectedBooks.push(bookId);
                bookItem.classList.add('selected');
            }
            
            // Update "All Books" selection
            const allBooksItem = document.querySelector('[data-book-id="all"]');
            if (this.selectedBooks.length === 0) {
                allBooksItem.classList.add('selected');
            } else {
                allBooksItem.classList.remove('selected');
            }
        }
    }

    setupEventListeners() {
        const form = document.getElementById('query-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitQuery();
        });
    }

    async submitQuery() {
        const question = document.getElementById('question').value.trim();
        const nResults = parseInt(document.getElementById('n-results').value);
        const useBookKnowledge = document.getElementById('use-book-knowledge').checked;
        
        if (!question) {
            this.showError('Please enter a question');
            return;
        }

        // Show loading modal
        const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        loadingModal.show();

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    book_ids: this.selectedBooks.length > 0 ? this.selectedBooks : [],
                    n_results: nResults,
                    use_book_knowledge: useBookKnowledge
                })
            });

            const data = await response.json();
            loadingModal.hide();

            if (data.success) {
                this.displayResults(data.result);
            } else {
                this.showError('Query failed: ' + data.error);
            }
        } catch (error) {
            loadingModal.hide();
            this.showError('Failed to submit query: ' + error.message);
        }
    }

    displayResults(result) {
        const resultsArea = document.getElementById('results-area');
        const queryStats = document.getElementById('query-stats');
        
        // Update query stats
        document.getElementById('processing-time').textContent = `${result.processing_time}s`;
        document.getElementById('context-length').textContent = `${result.context_length.toLocaleString()} chars`;
        document.getElementById('books-searched').textContent = `${result.books_searched.length} book(s)`;
        queryStats.style.display = 'block';

        // Display results
        resultsArea.innerHTML = `
            <div class="analysis-result">
                <h6>
                    <i class="fas fa-lightbulb me-2"></i>
                    Literary Analysis
                </h6>
                <div class="analysis-content">
                    ${this.formatAnswer(result.answer)}
                </div>
                <div class="mt-3">
                    ${result.books_searched.map(book => 
                        `<span class="book-badge me-2">${book}</span>`
                    ).join('')}
                </div>
            </div>
        `;

        // Scroll to results
        resultsArea.scrollIntoView({ behavior: 'smooth' });
    }

    formatAnswer(answer) {
        // Convert line breaks to HTML
        return answer.replace(/\n/g, '<br>');
    }

    showError(message) {
        const resultsArea = document.getElementById('results-area');
        resultsArea.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }

    updateStatusIndicator(status) {
        const indicator = document.getElementById('status-indicator');
        const icon = indicator.querySelector('i');
        const text = indicator.querySelector('span') || indicator;
        
        switch (status) {
            case 'ready':
                icon.className = 'fas fa-circle text-success me-1';
                text.textContent = 'Ready';
                break;
            case 'loading':
                icon.className = 'fas fa-circle text-warning me-1';
                text.textContent = 'Loading...';
                break;
            case 'error':
                icon.className = 'fas fa-circle text-danger me-1';
                text.textContent = 'Error';
                break;
        }
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new LiteraryAnalysisApp();
});
