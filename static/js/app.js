// Multi-Book Literary Analysis Frontend JavaScript

class LiteraryAnalysisApp {
    constructor() {
        this.selectedBooks = [];
        this.books = [];
        this.filteredBooks = [];
        this.currentFilter = 'all';
        this.searchTerm = '';
        this.init();
    }

    async init() {
        await this.loadBooks();
        await this.loadSystemStatus();
        this.setupEventListeners();
        this.setupSearchAndFilters();
    }

    async loadBooks() {
        try {
            const response = await fetch('/api/books');
            const data = await response.json();
            
            if (data.success) {
                this.books = data.books;
                this.filteredBooks = [...this.books];
                this.renderBooks();
                this.updateBookCount();
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
        
        if (this.filteredBooks.length === 0) {
            booksList.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-search fa-2x mb-2"></i>
                    <p>No books found matching your criteria</p>
                </div>
            `;
            return;
        }

        booksList.innerHTML = this.filteredBooks.map(book => {
            const isSelected = this.selectedBooks.includes(book.book_id);
            const isAllSelected = this.selectedBooks.length === 0;
            const selectedClass = (book.book_id === 'all' && isAllSelected) || isSelected ? 'selected' : '';
            
            return `
                <div class="book-item ${selectedClass}" data-book-id="${book.book_id}" onclick="app.toggleBookSelection('${book.book_id}')">
                    <div class="book-header">
                        <div class="book-title">${this.highlightSearchTerm(book.book_title)}</div>
                        <div class="book-actions">
                            <i class="fas fa-${isSelected || (book.book_id === 'all' && isAllSelected) ? 'check-circle' : 'circle'} text-primary"></i>
                        </div>
                    </div>
                    <div class="book-meta">
                        <div class="meta-item">
                            <i class="fas fa-file-alt me-1"></i>
                            ${book.chunk_count} chunks
                        </div>
                        <div class="meta-item">
                            <i class="fas fa-user me-1"></i>
                            ${book.author || 'Unknown Author'}
                        </div>
                        ${book.genre ? `
                        <div class="meta-item">
                            <i class="fas fa-tag me-1"></i>
                            ${book.genre}
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

        // Add "All Books" option at the top
        const totalChunks = this.books.reduce((sum, book) => sum + book.chunk_count, 0);
        const allBooksSelected = this.selectedBooks.length === 0;
        
        booksList.innerHTML = `
            <div class="book-item ${allBooksSelected ? 'selected' : ''}" data-book-id="all" onclick="app.toggleBookSelection('all')">
                <div class="book-header">
                    <div class="book-title">
                        <i class="fas fa-books me-2"></i>
                        All Books
                    </div>
                    <div class="book-actions">
                        <i class="fas fa-${allBooksSelected ? 'check-circle' : 'circle'} text-primary"></i>
                    </div>
                </div>
                <div class="book-meta">
                    <div class="meta-item">
                        <i class="fas fa-chart-bar me-1"></i>
                        ${totalChunks} total chunks
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-layer-group me-1"></i>
                        ${this.books.length} books
                    </div>
                </div>
            </div>
        ` + booksList.innerHTML;
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
        
        this.updateSelectedBooksIndicator();
    }

    setupEventListeners() {
        const form = document.getElementById('query-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitQuery();
        });

        // Clear button
        const clearBtn = document.getElementById('clear-btn');
        clearBtn.addEventListener('click', () => {
            this.clearForm();
        });
    }

    setupSearchAndFilters() {
        // Search functionality
        const searchInput = document.getElementById('book-search');
        searchInput.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.filterBooks();
        });

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                this.currentFilter = e.target.dataset.filter;
                this.filterBooks();
            });
        });
    }

    filterBooks() {
        let filtered = [...this.books];

        // Apply search filter
        if (this.searchTerm) {
            filtered = filtered.filter(book => 
                book.book_title.toLowerCase().includes(this.searchTerm) ||
                (book.author && book.author.toLowerCase().includes(this.searchTerm)) ||
                (book.genre && book.genre.toLowerCase().includes(this.searchTerm))
            );
        }

        // Apply category filter
        switch (this.currentFilter) {
            case 'selected':
                filtered = filtered.filter(book => this.selectedBooks.includes(book.book_id));
                break;
            case 'recent':
                // Sort by chunk count (assuming more chunks = more recent/important)
                filtered = filtered.sort((a, b) => b.chunk_count - a.chunk_count).slice(0, 5);
                break;
            case 'all':
            default:
                // No additional filtering
                break;
        }

        this.filteredBooks = filtered;
        this.renderBooks();
        this.updateBookCount();
    }

    highlightSearchTerm(text) {
        if (!this.searchTerm) return text;
        
        const regex = new RegExp(`(${this.searchTerm})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    updateBookCount() {
        const countElement = document.getElementById('book-count');
        countElement.textContent = this.filteredBooks.length;
    }

    updateSelectedBooksIndicator() {
        const indicator = document.getElementById('selected-count');
        if (this.selectedBooks.length === 0) {
            indicator.textContent = 'All books';
        } else {
            indicator.textContent = `${this.selectedBooks.length} book${this.selectedBooks.length > 1 ? 's' : ''}`;
        }
    }

    clearForm() {
        document.getElementById('question').value = '';
        document.getElementById('n-results').value = '80';
        document.getElementById('use-book-knowledge').checked = true;
        
        // Clear search
        document.getElementById('book-search').value = '';
        this.searchTerm = '';
        this.filterBooks();
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
