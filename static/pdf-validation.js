/**
 * PDF Validation Upload Handler
 *
 * Handles drag-and-drop file upload and validation task polling
 * for AR 25-50 compliance checking.
 */

(function () {
    'use strict';

    // DOM Elements
    const dropzone = document.getElementById('pdf-dropzone');
    const fileInput = document.getElementById('pdf-input');
    const selectedFileDiv = document.getElementById('selected-file');
    const selectedFilename = document.getElementById('selected-filename');
    const selectedFilesize = document.getElementById('selected-filesize');
    const removeFileBtn = document.getElementById('remove-file');
    const validateBtn = document.getElementById('validate-btn');
    const progressDiv = document.getElementById('validation-progress');
    const errorDiv = document.getElementById('validation-error');
    const errorMessage = document.getElementById('error-message');

    // State
    let selectedFile = null;

    // Initialize
    function init() {
        if (!dropzone || !fileInput) return;

        // Click to upload
        dropzone.addEventListener('click', () => fileInput.click());

        // File selection via input
        fileInput.addEventListener('change', handleFileSelect);

        // Drag and drop events
        dropzone.addEventListener('dragover', handleDragOver);
        dropzone.addEventListener('dragleave', handleDragLeave);
        dropzone.addEventListener('drop', handleDrop);

        // Remove file button
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', clearSelection);
        }

        // Validate button
        if (validateBtn) {
            validateBtn.addEventListener('click', startValidation);
        }
    }

    // Handle drag over
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
    }

    // Handle drag leave
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
    }

    // Handle drop
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    // Handle file input change
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    // Process selected file
    function processFile(file) {
        hideError();

        // Validate file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError('Please select a PDF file');
            return;
        }

        // Validate file size (10MB max)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            showError('File is too large. Maximum size is 10MB.');
            return;
        }

        selectedFile = file;
        showSelectedFile();
    }

    // Display selected file
    function showSelectedFile() {
        if (!selectedFile) return;

        selectedFilename.textContent = selectedFile.name;
        selectedFilesize.textContent = formatFileSize(selectedFile.size);

        dropzone.style.display = 'none';
        selectedFileDiv.style.display = 'flex';
        validateBtn.disabled = false;
    }

    // Clear file selection
    function clearSelection(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        selectedFile = null;
        fileInput.value = '';

        dropzone.style.display = 'block';
        selectedFileDiv.style.display = 'none';
        validateBtn.disabled = true;
        hideError();
    }

    // Start validation process
    async function startValidation() {
        if (!selectedFile) return;

        hideError();
        showProgress();
        validateBtn.disabled = true;

        try {
            // Upload file
            const formData = new FormData();
            formData.append('file', selectedFile);

            const uploadResponse = await fetch('/validate/pdf', {
                method: 'POST',
                body: formData,
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            const uploadResult = await uploadResponse.json();
            const taskId = uploadResult.task_id;

            // Poll for results
            await pollTaskStatus(taskId);

        } catch (error) {
            console.error('Validation error:', error);
            showError(error.message || 'Validation failed. Please try again.');
            hideProgress();
            validateBtn.disabled = false;
        }
    }

    // Poll task status until complete
    async function pollTaskStatus(taskId) {
        const maxAttempts = 60; // 60 attempts * 2 seconds = 2 minutes max
        let attempts = 0;

        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/validate/pdf/status/${taskId}`);
                const result = await response.json();

                if (result.state === 'SUCCESS') {
                    // Redirect to results page
                    window.location.href = `/validate/result/${result.result_id}`;
                    return;
                }

                if (result.state === 'FAILURE') {
                    throw new Error(result.error || 'Validation failed');
                }

                // Still pending, wait and try again
                await sleep(2000);
                attempts++;

            } catch (error) {
                throw error;
            }
        }

        throw new Error('Validation timed out. Please try again.');
    }

    // Show progress indicator
    function showProgress() {
        if (progressDiv) {
            progressDiv.style.display = 'block';
        }
        if (selectedFileDiv) {
            selectedFileDiv.style.display = 'none';
        }
    }

    // Hide progress indicator
    function hideProgress() {
        if (progressDiv) {
            progressDiv.style.display = 'none';
        }
        if (selectedFile && selectedFileDiv) {
            selectedFileDiv.style.display = 'flex';
        }
    }

    // Show error message
    function showError(message) {
        if (errorDiv && errorMessage) {
            errorMessage.textContent = message;
            errorDiv.style.display = 'flex';
        }
    }

    // Hide error message
    function hideError() {
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Sleep helper
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
