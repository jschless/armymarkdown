/**
 * Batch File Upload and Processing for Army Memo Maker
 */

class BatchUploader {
    constructor() {
        this.maxFiles = 5;
        this.maxFileSize = 50 * 1024; // 50KB
        this.selectedFiles = [];
        this.allowedTypes = ['.txt', '.md', '.text', '.markdown', '.amd', '.Amd'];

        this.init();
    }

    init() {
        // DOM elements with error checking
        this.modal = document.getElementById('batch-upload-modal');
        this.openBtn = document.getElementById('batch-upload-btn');
        this.closeBtn = document.getElementById('batch-modal-close');
        this.fileInput = document.getElementById('file-input');
        this.uploadArea = document.getElementById('file-upload-area');
        this.fileList = document.getElementById('file-list');
        this.selectedFilesList = document.getElementById('selected-files');
        this.clearBtn = document.getElementById('clear-files');
        this.processBtn = document.getElementById('process-files');
        this.progressDiv = document.getElementById('batch-progress');
        this.progressBar = document.getElementById('batch-progress-bar');
        this.statusDiv = document.getElementById('batch-status');
        this.resultsDiv = document.getElementById('batch-results');
        this.resultsList = document.getElementById('results-list');

        // Check for missing elements
        const requiredElements = {
            modal: this.modal,
            openBtn: this.openBtn,
            closeBtn: this.closeBtn,
            fileInput: this.fileInput,
            uploadArea: this.uploadArea,
            fileList: this.fileList,
            selectedFilesList: this.selectedFilesList,
            clearBtn: this.clearBtn,
            processBtn: this.processBtn,
            progressDiv: this.progressDiv,
            progressBar: this.progressBar,
            statusDiv: this.statusDiv,
            resultsDiv: this.resultsDiv,
            resultsList: this.resultsList
        };

        for (const [name, element] of Object.entries(requiredElements)) {
            if (!element) {
                console.error(`BatchUploader: Missing element ${name} (${name === 'modal' ? 'batch-upload-modal' : name === 'openBtn' ? 'batch-upload-btn' : name === 'closeBtn' ? 'batch-modal-close' : 'unknown-id'})`);
                return; // Don't bind events if elements are missing
            }
        }

        this.bindEvents();
    }

    bindEvents() {
        // Modal controls
        this.openBtn.addEventListener('click', () => this.openModal());
        this.closeBtn.addEventListener('click', () => this.closeModal());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        // File selection
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));

        // Actions
        this.clearBtn.addEventListener('click', () => this.clearFiles());
        this.processBtn.addEventListener('click', () => this.processFiles());
    }

    openModal() {
        this.modal.style.display = 'flex';
        this.resetModal();
    }

    closeModal() {
        this.modal.style.display = 'none';
    }

    resetModal() {
        this.clearFiles();
        this.progressDiv.style.display = 'none';
        this.resultsDiv.style.display = 'none';
        this.fileList.style.display = 'none';
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        this.uploadArea.style.borderColor = 'var(--color-primary)';
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        this.uploadArea.style.borderColor = 'var(--color-border)';

        const files = Array.from(e.dataTransfer.files);
        this.addFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
    }

    addFiles(files) {
        for (const file of files) {
            if (this.selectedFiles.length >= this.maxFiles) {
                this.showError(`Maximum ${this.maxFiles} files allowed`);
                break;
            }

            if (!this.isValidFile(file)) {
                continue;
            }

            // Check for duplicates
            if (this.selectedFiles.some(f => f.name === file.name)) {
                this.showError(`File "${file.name}" already selected`);
                continue;
            }

            this.selectedFiles.push(file);
        }

        this.updateFileList();
        this.fileInput.value = ''; // Reset input
    }

    isValidFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            this.showError(`File "${file.name}" is too large (max 50KB)`);
            return false;
        }

        // Check file type - be more permissive
        const filename = file.name.toLowerCase();
        const extension = '.' + filename.split('.').pop();

        // Allow files without extension if they might be text
        const isTextFile = this.allowedTypes.includes(extension) ||
                          file.type.includes('text') ||
                          filename.includes('txt') ||
                          extension === '';

        if (!isTextFile) {
            this.showError(`File "${file.name}" has unsupported type. Use text files like ${this.allowedTypes.join(', ')}`);
            return false;
        }

        return true;
    }

    updateFileList() {
        if (this.selectedFiles.length === 0) {
            this.fileList.style.display = 'none';
            this.processBtn.disabled = true;
            return;
        }

        this.fileList.style.display = 'block';
        this.processBtn.disabled = false;

        this.selectedFilesList.innerHTML = '';
        this.selectedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div>
                    <strong>${file.name}</strong>
                    <small style="color: var(--color-gray-500); margin-left: 8px;">
                        ${this.formatFileSize(file.size)}
                    </small>
                </div>
                <button class="remove-file" data-index="${index}" style="
                    background: none;
                    border: none;
                    color: var(--color-error);
                    cursor: pointer;
                    padding: 4px;
                ">✕</button>
            `;

            const removeBtn = li.querySelector('.remove-file');
            removeBtn.addEventListener('click', () => this.removeFile(index));

            this.selectedFilesList.appendChild(li);
        });
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileList();
    }

    clearFiles() {
        this.selectedFiles = [];
        this.updateFileList();
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        return Math.round(bytes / 1024) + ' KB';
    }

    async processFiles() {
        if (this.selectedFiles.length === 0) return;

        this.progressDiv.style.display = 'block';
        this.resultsDiv.style.display = 'none';
        this.processBtn.disabled = true;

        const results = [];

        for (let i = 0; i < this.selectedFiles.length; i++) {
            const file = this.selectedFiles[i];
            const progress = ((i + 1) / this.selectedFiles.length) * 100;

            this.progressBar.style.width = progress + '%';
            this.statusDiv.textContent = `Processing ${file.name}...`;

            try {
                const content = await this.readFileContent(file);
                const result = await this.processFile(file.name, content);

                results.push({
                    filename: file.name,
                    success: true,
                    url: result.url,
                    message: 'Successfully processed'
                });

            } catch (error) {
                results.push({
                    filename: file.name,
                    success: false,
                    error: error.message
                });
            }
        }

        this.showResults(results);
        this.processBtn.disabled = false;
    }

    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    async processFile(filename, content) {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                memo_text: content
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // The /process endpoint returns a text message and puts task ID in Location header
        const locationHeader = response.headers.get('Location');

        if (!locationHeader) {
            throw new Error('No Location header found in response');
        }

        // Extract task ID from URL like "/status/task_id"
        const taskIdMatch = locationHeader.match(/\/status\/(.+)$/);
        if (!taskIdMatch) {
            throw new Error('Could not extract task ID from Location header');
        }

        const taskId = taskIdMatch[1];

        // Wait for processing to complete
        return await this.waitForCompletion(taskId);
    }

    async waitForCompletion(taskId) {
        const maxAttempts = 30; // 30 seconds max
        let attempts = 0;

        while (attempts < maxAttempts) {
            const response = await fetch(`/status/${taskId}`, {
                method: 'GET'
            });

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            const responseText = await response.text();

            let result;
            try {
                result = JSON.parse(responseText);
            } catch (e) {
                throw new Error('Invalid status response format');
            }

            if (result.state === 'SUCCESS') {
                // The PDF URL can be in presigned_url or result field
                const pdfUrl = result.presigned_url || result.result;

                if (!pdfUrl) {
                    throw new Error('No PDF URL found in successful result');
                }

                return {
                    url: pdfUrl
                };
            }

            if (result.state === 'FAILURE') {
                throw new Error(result.status || 'Processing failed');
            }

            // Wait 1 second before next check
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;
        }

        throw new Error('Processing timeout');
    }

    showResults(results) {
        this.progressDiv.style.display = 'none';
        this.resultsDiv.style.display = 'block';

        this.resultsList.innerHTML = '';

        results.forEach(result => {
            const li = document.createElement('li');

            if (result.success) {
                li.innerHTML = `
                    <div class="result-success">
                        ✅ <strong>${result.filename}</strong> - ${result.message}
                        <div style="margin-top: 4px;">
                            <a href="${result.url}" target="_blank" class="modern-btn modern-btn-sm modern-btn-outline">
                                Download PDF
                            </a>
                        </div>
                    </div>
                `;
            } else {
                li.innerHTML = `
                    <div class="result-error">
                        ❌ <strong>${result.filename}</strong> - ${result.error}
                    </div>
                `;
            }

            this.resultsList.appendChild(li);
        });
    }

    showError(message) {
        if (window.showStatusMessage) {
            window.showStatusMessage(message, 'error');
        } else {
            alert(message);
        }
    }
}

// Initialize batch uploader when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('batch-upload-btn')) {
        window.batchUploader = new BatchUploader();
    }
});
