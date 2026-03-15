document.getElementById('linkSelector').addEventListener('change', function() {
    const selectElement = document.getElementById('linkSelector');
    const selectedValue = selectElement.options[selectElement.selectedIndex].value;

    window.location.assign(selectedValue);
});

function saveData() {
    const formData = new FormData(document.getElementById('memo'));

    fetch('/save_progress', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest' // Add header to indicate AJAX request
        }
    })
        .then(response => {
            if (!response.ok) {
                // Only log errors, not successful saves
                console.error('Error submitting form data:', response.status);
            }
        })
        .catch(error => {
            console.error('Error submitting form data:', error);
        });
}

function buttonPress(endpoint) {
    const formData = new FormData(document.getElementById('memo'));
    const previewWindow = window.open('', '_blank');

    // Show modern progress modal with indeterminate progress
    showProgress(true);
    showIndeterminateProgress();

    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(async response => {
            if (!response.ok) {
                throw new Error(await extractErrorMessage(response));
            }

            const contentType = response.headers.get('Content-Type') || '';
            if (!contentType.includes('application/pdf')) {
                throw new Error('Unexpected response type from memo generation.');
            }

            return {
                blob: await response.blob(),
                filename: getPdfFilename(response)
            };
        })
        .then(({ blob, filename }) => {
            const pdfUrl = window.URL.createObjectURL(blob);

            showProgress(false);
            openPdfResult(pdfUrl, previewWindow, filename);
            showStatusMessage('🎉 Your memo has been created successfully! The PDF should open in a new tab.', 'success');

            window.setTimeout(() => window.URL.revokeObjectURL(pdfUrl), 60000);
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            if (previewWindow && !previewWindow.closed) {
                previewWindow.close();
            }
            showProgress(false);
            showStatusMessage(error.message || 'Error submitting your memo. Please check your connection and try again.', 'error');
        });
}

async function extractErrorMessage(response) {
    const contentType = response.headers.get('Content-Type') || '';

    if (contentType.includes('application/json')) {
        const payload = await response.json();
        return payload.error || payload.status || `HTTP ${response.status}`;
    }

    const text = await response.text();
    if (text && text.trim().length > 0) {
        return text;
    }

    return `HTTP ${response.status}: ${response.statusText}`;
}

function getPdfFilename(response) {
    const contentDisposition = response.headers.get('Content-Disposition') || '';
    const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match) {
        return decodeURIComponent(utf8Match[1]);
    }

    const basicMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
    if (basicMatch) {
        return basicMatch[1];
    }

    return response.headers.get('X-Memo-Filename') || 'memo.pdf';
}

function openPdfResult(pdfUrl, previewWindow, filename) {
    if (previewWindow && !previewWindow.closed) {
        previewWindow.location = pdfUrl;
        previewWindow.document.title = filename;
        return;
    }

    const link = document.createElement('a');
    link.href = pdfUrl;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.click();
}

document.addEventListener('DOMContentLoaded', function() {
    const exampleFile = window.location.pathname + window.location.search;
    const linkSelector = document.getElementById('linkSelector');

    for (let i = 0; i < linkSelector.options.length; i++) {
        const option = linkSelector.options[i];
        if (option.value === exampleFile) {
            option.selected = true;
            break;
        }
    }
});

function makeTabsWork(textAreaId) {
    const textarea = document.getElementById(textAreaId);

    textarea.addEventListener('keydown', function(event) {
        if (event.key === 'Tab') {
            event.preventDefault();

            const start = this.selectionStart;
            const end = this.selectionEnd;

            // Insert four spaces at the caret position
            this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);

            // Move the caret position forward by four spaces
            this.selectionStart = this.selectionEnd = start + 4;
        }
    });
}

// Function to show/hide progress modal
function showProgress(show = true) {
    const modal = document.getElementById('progress-modal');
    const overlay = document.getElementById('progress-overlay');

    if (modal && overlay) {
        if (show) {
            overlay.style.display = 'block';
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        } else {
            overlay.style.display = 'none';
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
}

// Function to show status messages
function showStatusMessage(message, type = 'info') {
    const statusAlert = document.getElementById('status-alert');
    const statusElement = document.getElementById('status');

    if (statusAlert && statusElement) {
        statusElement.textContent = message;
        statusAlert.className = `modern-alert modern-alert-${type} fade-in`;
        statusAlert.style.display = 'flex';

        // Auto-hide after 5 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                statusAlert.style.display = 'none';
            }, 5000);
        }
    }
}

// Function to show indeterminate progress (just animations, no percentages)
function showIndeterminateProgress() {
    const progressText = document.getElementById('progress-percentage');
    if (progressText) {
        progressText.textContent = 'Processing...';
        progressText.style.fontSize = 'var(--font-size-base)';
        progressText.style.fontWeight = 'var(--font-weight-medium)';
    }

    // Show the progress fill for indeterminate progress
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        progressFill.style.width = '100%';
    }
}

window.updateProgress = function() {
    showIndeterminateProgress();
};
