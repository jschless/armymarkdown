/* global AbortController, FormData, clearTimeout, document, fetch, setTimeout, window */
(function () {
    'use strict';

    const DEBOUNCE_MS = 700;

    function initLiveReview() {
        const form = document.getElementById('memo');
        const panel = document.getElementById('live-review-panel');
        const summary = document.getElementById('live-review-summary');
        const findings = document.getElementById('live-review-findings');
        const status = document.getElementById('live-review-status');

        if (!form || !panel || !summary || !findings || !status) {
            return;
        }

        let debounceTimer = null;
        let activeController = null;
        let requestSequence = 0;

        function setStatus(message, tone = 'idle') {
            status.textContent = message;
            status.className = `memo-live-review-status memo-live-review-status-${tone}`;
            panel.dataset.reviewTone = tone;
        }

        function renderIdleState(message) {
            setStatus(message, 'idle');
            summary.innerHTML = '';
            findings.innerHTML = `
                <div class="review-empty-state">
                    <p>${escapeHtml(message)}</p>
                </div>
            `;
        }

        async function runReview() {
            const localRequestId = ++requestSequence;
            const formData = new FormData(form);

            if (activeController) {
                activeController.abort();
            }
            activeController = new AbortController();

            panel.classList.add('memo-live-review-loading');
            setStatus('Checking live memo review…', 'loading');

            try {
                const response = await fetch('/review/memo/live', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    signal: activeController.signal
                });

                if (!response.ok) {
                    throw new Error(await extractReviewError(response));
                }

                const report = await response.json();
                if (localRequestId !== requestSequence) {
                    return;
                }

                panel.classList.remove('memo-live-review-loading');
                setStatus(report.passed ? 'Live review passed' : 'Live review found issues', report.passed ? 'success' : 'warning');
                window.renderReviewResults(summary, findings, report, {
                    mode: 'document',
                    emptyMessage: 'No live review findings were reported. Use Review Memo for rendered layout checks.'
                });
            } catch (error) {
                if (error.name === 'AbortError') {
                    return;
                }
                panel.classList.remove('memo-live-review-loading');
                setStatus('Live review unavailable', 'error');
                summary.innerHTML = '';
                findings.innerHTML = `
                    <div class="review-empty-state">
                        <p>${escapeHtml(error.message || 'Live review could not be completed.')}</p>
                    </div>
                `;
            }
        }

        function scheduleReview() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(runReview, DEBOUNCE_MS);
        }

        form.addEventListener('input', scheduleReview);
        form.addEventListener('change', scheduleReview);

        renderIdleState('Live review will update as you edit. Use Review Memo for rendered layout checks.');
        setTimeout(runReview, 200);
    }

    async function extractReviewError(response) {
        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('application/json')) {
            const payload = await response.json();
            return payload.error || `HTTP ${response.status}`;
        }
        const text = await response.text();
        return text || `HTTP ${response.status}: ${response.statusText}`;
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll('\'', '&#39;');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLiveReview);
    } else {
        initLiveReview();
    }
})();
