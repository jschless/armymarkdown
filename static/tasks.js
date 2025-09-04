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

    console.log('Calling buttonPress on endpoint');
    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest' // Add header to indicate AJAX request
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
            document.getElementById('status').textContent = 
            'Error submitting your memo. Please check your connection and try again.';
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
                document.getElementById('status').textContent = ''; 
                // Create a button to retrieve memo on user click
                const button = document.createElement('button');
                button.textContent = 'Click to open memo';
                button.addEventListener('click', function() {
                    window.open(data['presigned_url'], '_blank', 'noopener,noreferrer'); // Security enhancement
                    document.getElementById('progress-bar').style.width = '100%';
                    document.getElementById('progress-bar-container').style.display = 'none';
                    document.getElementById('progress-bar-container').style.opacity = '0.5';
                    document.getElementById('progress').style.width = '0%';
                    document.getElementById('temp_button').remove();
                });

                button.style.margin = '20px';
                button.classList.add('center');
                button.setAttribute('id', 'temp_button');

                const container = document.getElementById('progress-bar-container');
                container.style.opacity = '1';
                container.append(document.createElement('br'));
                container.appendChild(button);
            } else if (data['state'] === 'FAILURE') {
                let errorMessage = 'Error processing your memo. ';
                if (data['status']) {
                // Try to provide more specific error information
                    if (data['status'].includes('VALIDATION ERROR')) {
                        errorMessage += 'Please check your memo format and required fields.';
                    } else if (data['status'].includes('LaTeX')) {
                        errorMessage += 'There was an issue generating the PDF. Please check your formatting.';
                    } else if (data['status'].includes('S3') || data['status'].includes('upload')) {
                        errorMessage += 'There was an issue saving your document. Please try again.';
                    } else {
                        errorMessage += 'Please check your memo format and try again.';
                    }
                } else {
                    errorMessage += 'Please check your memo format and try again.';
                }
                document.getElementById('status').textContent = errorMessage;
            } else {
                document.getElementById('progress-bar-container').style.display = 'block';

                // Constants for polling
                const POLLING_INTERVAL_MS = 1000;
                const AVERAGE_COMPLETION_SECONDS = 10;
                const MAX_POLLING_ATTEMPTS = 80;
            
                count += 1;

                // Rerun in 1 second
                if (count < MAX_POLLING_ATTEMPTS) {
                    const progress = Math.min(count / AVERAGE_COMPLETION_SECONDS * 100, 100);
                    document.getElementById('progress').style.width = progress + '%';
                
                    setTimeout(function() {
                        updateProgress(status_url, count);
                    }, POLLING_INTERVAL_MS);
                } else {
                // Timeout after max attempts
                    document.getElementById('status').textContent = 
                    'Processing is taking longer than expected. Please try again or contact support if the issue persists.';
                }
            }
        })
        .catch(error => {
            console.error('Error polling task status:', error);
            document.getElementById('status').textContent = 
            'Connection error while checking status. Please refresh the page and try again.';
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
