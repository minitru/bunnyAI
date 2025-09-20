// Bunny AI Frontend JavaScript

class BunnyAI {
    constructor() {
        this.init();
    }

    async init() {
        this.setupEventListeners();
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

    async submitQuery() {
        const question = document.getElementById('question').value.trim();
        
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
                    question: question
                })
            });

            const data = await response.json();
            loadingModal.hide();

            if (data.success) {
                this.displayResults(data);
            } else {
                this.showError('Query failed: ' + data.error);
            }
        } catch (error) {
            loadingModal.hide();
            this.showError('Failed to submit query: ' + error.message);
        }
    }

    displayResults(data) {
        const resultsArea = document.getElementById('results-area');
        const queryStats = document.getElementById('query-stats');
        
        // Update query stats
        document.getElementById('processing-time').textContent = `${data.processing_time}s`;
        document.getElementById('context-length').textContent = `${data.context_length.toLocaleString()} chars`;
        queryStats.style.display = 'block';

        // Display results
        resultsArea.innerHTML = `
            <div class="analysis-result">
                <div class="analysis-content">
                    ${this.formatAnswer(data.answer)}
                </div>
            </div>
        `;

        // Scroll to results
        resultsArea.scrollIntoView({ behavior: 'smooth' });
    }

    formatAnswer(answer) {
        // Convert line breaks to HTML and format paragraphs
        return answer
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
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

    clearForm() {
        document.getElementById('question').value = '';
        document.getElementById('results-area').innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-comments fa-3x mb-3"></i>
                <p>Ask a question to get started</p>
            </div>
        `;
        document.getElementById('query-stats').style.display = 'none';
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new BunnyAI();
});