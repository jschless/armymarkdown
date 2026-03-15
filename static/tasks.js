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

    // Show modern progress modal with indeterminate progress
    setProgressContent(
        'Creating your memo...',
        'Compiling Typst document',
        'Your document is being processed on our servers'
    );
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
            const opened = openPdfResult(pdfUrl, filename);
            if (opened) {
                displayStatusMessage('Your memo has been created successfully. The PDF opened in a new tab.', 'success');
            } else {
                displayStatusMessage(
                    'Your memo is ready. Your browser blocked the automatic tab open.',
                    'success',
                    {
                        autoHide: false,
                        actions: [
                            {
                                label: 'Open PDF',
                                href: pdfUrl,
                                target: '_blank',
                                rel: 'noopener noreferrer'
                            },
                            {
                                label: 'Download PDF',
                                href: pdfUrl,
                                download: filename
                            }
                        ]
                    }
                );
            }

            window.setTimeout(() => window.URL.revokeObjectURL(pdfUrl), 60000);
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            showProgress(false);
            displayStatusMessage(error.message || 'Error submitting your memo. Please check your connection and try again.', 'error');
        });
}

async function reviewMemo(endpoint) {
    const formData = new FormData(document.getElementById('memo'));

    setProgressContent(
        'Reviewing your memo...',
        'Running AR 25-50 checks',
        'We are rendering the memo and reviewing the resulting layout'
    );
    showProgress(true);
    showIndeterminateProgress();

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(await extractErrorMessage(response));
        }

        const report = await response.json();
        showProgress(false);
        renderReviewModal(report);
    } catch (error) {
        console.error('Error reviewing memo:', error);
        showProgress(false);
        displayStatusMessage(error.message || 'Error reviewing your memo. Please try again.', 'error');
    }
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

function openPdfResult(pdfUrl, filename) {
    const openedWindow = window.open(pdfUrl, '_blank', 'noopener,noreferrer');
    if (openedWindow) {
        try {
            openedWindow.document.title = filename;
        } catch (error) {
            console.debug('Could not update opened PDF tab title:', error);
        }
        return true;
    }
    return false;
}

function renderReviewModal(report) {
    const modal = document.getElementById('review-modal');
    const summary = document.getElementById('review-summary');
    const findings = document.getElementById('review-findings');
    if (!modal || !summary || !findings) {
        displayStatusMessage('Review completed, but the results dialog is unavailable on this page.', 'warning');
        return;
    }

    const failedFindings = (report.findings || []).filter((finding) => finding.status === 'fail');
    const severityCounts = report.failing_severity_counts || {};
    const errorCount = severityCounts.error || 0;
    const warningCount = severityCounts.warning || 0;

    summary.innerHTML = `
        <div class="review-summary-card ${report.passed ? 'review-summary-pass' : 'review-summary-fail'}">
            <div class="review-summary-main">
                <span class="review-summary-badge">${report.passed ? 'Passed' : 'Needs Review'}</span>
                <div class="review-summary-copy">
                    <strong>${report.passed ? 'This memo passed the rendered AR 25-50 review.' : 'This memo has rendered review findings that need attention.'}</strong>
                    <p>${errorCount} error(s), ${warningCount} warning(s), ${report.passing_rules || 0} passing check(s).</p>
                </div>
            </div>
        </div>
    `;

    if (failedFindings.length === 0) {
        findings.innerHTML = `
            <div class="review-empty-state">
                <p>No failing findings were reported. The rendered memo matched the active review rules.</p>
            </div>
        `;
    } else {
        findings.innerHTML = failedFindings.map((finding) => `
            <div class="review-finding review-finding-${escapeHtml(finding.severity || 'warning')}">
                <div class="review-finding-header">
                    <span class="review-finding-badge">${escapeHtml((finding.severity || 'warning').toUpperCase())}</span>
                    <strong>${escapeHtml(finding.name || finding.rule_name || finding.rule_id)}</strong>
                </div>
                <p class="review-finding-message">${escapeHtml(finding.message || '')}</p>
                ${finding.suggested_fix ? `<p class="review-finding-fix"><strong>Suggested fix:</strong> ${escapeHtml(finding.suggested_fix)}</p>` : ''}
                ${finding.ar_reference ? `<p class="review-finding-reference">${escapeHtml(finding.ar_reference)}</p>` : ''}
            </div>
        `).join('');
    }

    modal.style.display = 'flex';
}

function closeReviewModal() {
    const modal = document.getElementById('review-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll('\'', '&#39;');
}

document.addEventListener('DOMContentLoaded', function() {
    const exampleFile = window.location.pathname + window.location.search;
    const linkSelector = document.getElementById('linkSelector');
    const reviewModal = document.getElementById('review-modal');
    const reviewModalClose = document.getElementById('review-modal-close');

    for (let i = 0; i < linkSelector.options.length; i++) {
        const option = linkSelector.options[i];
        if (option.value === exampleFile) {
            option.selected = true;
            break;
        }
    }

    if (reviewModalClose) {
        reviewModalClose.addEventListener('click', closeReviewModal);
    }

    if (reviewModal) {
        reviewModal.addEventListener('click', function(event) {
            if (event.target === reviewModal) {
                closeReviewModal();
            }
        });
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

function setProgressContent(title, status, detail) {
    const titleElement = document.getElementById('progress-title');
    const statusElement = document.getElementById('progress-status');
    const detailElement = document.querySelector('#progress-modal .text-sm:last-of-type');

    if (titleElement) {
        titleElement.textContent = title;
    }
    if (statusElement) {
        statusElement.textContent = status;
    }
    if (detailElement) {
        detailElement.textContent = detail;
    }
}

// Function to show status messages
function displayStatusMessage(message, type = 'info', options = {}) {
    if (window.showStatusMessage) {
        window.showStatusMessage(message, type, options);
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

window.reviewMemo = reviewMemo;
