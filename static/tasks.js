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
            if (response.ok) {
                console.log('Form data submitted successfully.');
            } else {
                console.error('Error submitting form data:', response.status);
            }
        })
        .catch(error => {
            console.error('Error submitting form data:', error);
        });
}

function buttonPress(endpoint, polling_function) {
    const formData = new FormData(document.getElementById('memo'));
    
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
        .then(response => {
            if (response.ok) {
                return response.headers.get('Location');
            } else {
                throw new Error('Network response was not ok');
            }
        })
        .then(status_url => {
            polling_function(status_url, 0);
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            showProgress(false);
            showStatusMessage('Error submitting your memo. Please check your connection and try again.', 'error');
        });
}

function updateProgress(status_url, count) {
    fetch(status_url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json(); 
        })
        .then(data => {
            if (data['state'] === 'SUCCESS') {
            // Hide progress modal and show success
                showProgress(false);
            
                // Open PDF in new tab
                if (data['presigned_url']) {
                    window.open(data['presigned_url'], '_blank', 'noopener,noreferrer');
                }
            
                // Show success message
                showStatusMessage('🎉 Your memo has been created successfully! The PDF should open in a new tab.', 'success');
            
            } else if (data['state'] === 'FAILURE') {
            // Hide progress modal
                showProgress(false);
            
                const errorMessage = 'Error processing your memo. Please check your memo format and try again.';
            
                // Show error message using modern alert system
                showStatusMessage(errorMessage, 'error');
            } else {
            // Still processing - update progress
                const POLLING_INTERVAL_MS = 1000;        
                const MAX_POLLING_ATTEMPTS = 80;
            
                count += 1;

                // Keep showing indeterminate progress (no percentage updates needed)
            

                // Continue polling or timeout
                if (count < MAX_POLLING_ATTEMPTS) {
                    setTimeout(function () {
                        updateProgress(status_url, count); 
                    }, POLLING_INTERVAL_MS);
                } else {
                // Timeout after max attempts
                    showProgress(false);
                    showStatusMessage('Processing is taking longer than expected. Please try again or contact support if the issue persists.', 'warning');
                }
            }
        })
        .catch(error => {
            console.error('Error polling task status:', error);
            showProgress(false);
            showStatusMessage('Connection error while checking status. Please refresh the page and try again.', 'error');
        });
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
    
    // Hide the progress fill since we're using CSS animations
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        progressFill.style.width = '0%';
    }
}
