/* global clearTimeout, setTimeout, document, window, getComputedStyle, console */
/**
 * Real-time Validation for Text Editor (AMD Format)
 *
 * Parses AMD format text and shows validation hints in a panel.
 * Does NOT block form submission - purely informational.
 */

(function () {
    'use strict';

    // Wait for validation rules to load
    if (typeof window.MemoValidationRules === 'undefined') {
        console.warn('MemoValidationRules not loaded');
        return;
    }

    const Rules = window.MemoValidationRules;

    // Debounce timer
    let debounceTimer = null;
    const DEBOUNCE_DELAY = 750;

    // DOM elements
    let editor = null;
    let validationPanel = null;

    // Initialize
    function init() {
        editor = document.getElementById('editor');
        if (!editor) return;

        // Create validation panel
        createValidationPanel();

        // Attach event listeners
        editor.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(validateText, DEBOUNCE_DELAY);
        });

        editor.addEventListener('blur', validateText);

        // Initial validation
        setTimeout(validateText, 500);
    }

    // Create the validation hints panel
    function createValidationPanel() {
    // Create panel container
        validationPanel = document.createElement('div');
        validationPanel.id = 'text-validation-panel';
        validationPanel.className = 'text-validation-panel';
        validationPanel.innerHTML = `
      <div class="validation-panel-header">
        <span class="validation-panel-title">AR 25-50 Validation</span>
        <button type="button" class="validation-panel-toggle" aria-label="Toggle validation panel">
          <span class="toggle-icon">▼</span>
        </button>
      </div>
      <div class="validation-panel-content">
        <div class="validation-status">
          <span class="status-icon">✓</span>
          <span class="status-text">Checking...</span>
        </div>
        <ul class="validation-issues" id="field-issues"></ul>
        <div class="spelling-section" id="spelling-section" style="display: none;">
          <h4 class="spelling-section-title">Spelling</h4>
          <ul class="spelling-issues" id="spelling-issues"></ul>
        </div>
      </div>
    `;

        // Insert after the editor's parent form group
        const formGroup = editor.closest('.modern-form-group');
        if (formGroup) {
            formGroup.parentNode.insertBefore(validationPanel, formGroup.nextSibling);
        } else {
            editor.parentNode.insertBefore(validationPanel, editor.nextSibling);
        }

        // Toggle functionality
        const toggleBtn = validationPanel.querySelector('.validation-panel-toggle');
        const content = validationPanel.querySelector('.validation-panel-content');
        const toggleIcon = validationPanel.querySelector('.toggle-icon');

        toggleBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const isCollapsed = content.style.display === 'none';
            content.style.display = isCollapsed ? 'block' : 'none';
            toggleIcon.textContent = isCollapsed ? '▼' : '▶';
            validationPanel.classList.toggle('collapsed', !isCollapsed);
        });
    }

    // Validate the text content
    function validateText() {
        if (!editor || !validationPanel) return;

        const text = editor.value;

        // Parse fields and validate header fields only
        // (Body text formatting is handled automatically by the generator)
        const fields = Rules.parseAmdText(text);
        const fieldIssues = Rules.validateAll(fields);

        // Get text to spellcheck (subject + body)
        const subjectText = fields['SUBJECT'] || '';
        const bodyText = fields._BODY_TEXT || '';
        const textToCheck = subjectText + ' ' + bodyText;

        // Validate spelling
        const spellingErrors = Rules.validateSpelling(textToCheck);

        updateValidationPanel(fieldIssues, fields, spellingErrors);
    }

    // Update the validation panel with results
    function updateValidationPanel(fieldIssues, fields, spellingErrors) {
        const statusIcon = validationPanel.querySelector('.status-icon');
        const statusText = validationPanel.querySelector('.status-text');
        const fieldIssuesList = validationPanel.querySelector('#field-issues');
        const spellingSection = validationPanel.querySelector('#spelling-section');
        const spellingIssuesList = validationPanel.querySelector('#spelling-issues');

        const fieldEntries = Object.entries(fieldIssues);
        spellingErrors = spellingErrors || [];

        const totalErrors = fieldEntries.filter(([, i]) => i.severity === 'error').length;
        const totalWarnings = fieldEntries.filter(([, i]) => i.severity === 'warning').length;
        const totalSpellingIssues = spellingErrors.length;

        // Build status parts
        const statusParts = [];
        if (totalErrors > 0) {
            statusParts.push(`${totalErrors} error${totalErrors > 1 ? 's' : ''}`);
        }
        if (totalWarnings > 0) {
            statusParts.push(`${totalWarnings} warning${totalWarnings > 1 ? 's' : ''}`);
        }
        if (totalSpellingIssues > 0) {
            statusParts.push(`${totalSpellingIssues} spelling issue${totalSpellingIssues > 1 ? 's' : ''}`);
        }

        // Update status
        if (totalErrors > 0) {
            statusIcon.textContent = '✗';
            statusIcon.className = 'status-icon status-error';
            statusText.textContent = statusParts.join(', ');
            validationPanel.className = 'text-validation-panel has-errors';
        } else if (totalWarnings > 0 || totalSpellingIssues > 0) {
            statusIcon.textContent = '⚠';
            statusIcon.className = 'status-icon status-warning';
            statusText.textContent = statusParts.join(', ');
            validationPanel.className = 'text-validation-panel has-warnings';
        } else {
            statusIcon.textContent = '✓';
            statusIcon.className = 'status-icon status-success';
            statusText.textContent = 'All checks passed';
            validationPanel.className = 'text-validation-panel';
        }

        // Build field issues list
        fieldIssuesList.innerHTML = '';

        if (fieldEntries.length === 0) {
            const li = document.createElement('li');
            li.className = 'validation-issue validation-success';
            li.innerHTML = '<span class="issue-message">All header fields valid</span>';
            fieldIssuesList.appendChild(li);
        } else {
            // Sort: errors first, then warnings
            fieldEntries.sort((a, b) => {
                if (a[1].severity === 'error' && b[1].severity !== 'error') return -1;
                if (a[1].severity !== 'error' && b[1].severity === 'error') return 1;
                return 0;
            });

            fieldEntries.forEach(([fieldName, issue]) => {
                const li = document.createElement('li');
                li.className = `validation-issue validation-${issue.severity}`;

                const fieldLabel = formatFieldName(fieldName);
                const currentValue = fields[fieldName] || '(empty)';

                li.innerHTML = `
          <span class="issue-severity ${issue.severity}">${issue.severity === 'error' ? '✗' : '⚠'}</span>
          <span class="issue-field">${fieldLabel}</span>
          <span class="issue-message">${issue.message}</span>
          <span class="issue-value" title="${escapeHtml(currentValue)}">${truncate(currentValue, 30)}</span>
        `;

                // Click to find field in editor
                li.addEventListener('click', function () {
                    highlightFieldInEditor(fieldName);
                });

                fieldIssuesList.appendChild(li);
            });
        }

        // Update spelling section
        if (spellingErrors.length > 0) {
            spellingSection.style.display = 'block';
            spellingSection.querySelector('.spelling-section-title').textContent =
                `Spelling (${spellingErrors.length} issue${spellingErrors.length > 1 ? 's' : ''})`;
            spellingIssuesList.innerHTML = '';

            spellingErrors.forEach(error => {
                const li = document.createElement('li');
                li.className = 'spelling-issue';
                li.setAttribute('data-word', error.word);

                const suggestionsText = error.suggestions.length
                    ? `<span class="spelling-suggestions">\u2192 ${error.suggestions.join(', ')}</span>`
                    : '';

                li.innerHTML = `
                    <span class="misspelled-word">${escapeHtml(error.word)}</span>
                    ${suggestionsText}
                `;

                // Click to find word in editor
                li.addEventListener('click', function () {
                    highlightWordInEditor(error.word);
                });

                spellingIssuesList.appendChild(li);
            });
        } else {
            spellingSection.style.display = 'none';
        }
    }

    // Highlight a word in the editor
    function highlightWordInEditor(word) {
        if (!editor) return;

        const text = editor.value;
        // Case-insensitive search for the word
        const regex = new RegExp('\\b' + word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
        const match = text.match(regex);

        if (match) {
            const startIndex = text.search(regex);
            const endIndex = startIndex + match[0].length;

            editor.focus();
            editor.setSelectionRange(startIndex, endIndex);

            // Scroll to selection
            const lineNumber = text.substring(0, startIndex).split('\n').length;
            const lineHeight = parseInt(getComputedStyle(editor).lineHeight) || 20;
            editor.scrollTop = (lineNumber - 3) * lineHeight;
        }
    }

    // Format field name for display
    function formatFieldName(fieldName) {
        const names = {
            'ORGANIZATION_NAME': 'Org Name',
            'ORGANIZATION_STREET_ADDRESS': 'Street Address',
            'ORGANIZATION_CITY_STATE_ZIP': 'City/State/ZIP',
            'OFFICE_SYMBOL': 'Office Symbol',
            'DATE': 'Date',
            'SUBJECT': 'Subject',
            'AUTHOR': 'Author',
            'RANK': 'Rank',
            'BRANCH': 'Branch',
            'TITLE': 'Title',
            'SUSPENSE': 'Suspense',
            'MEMO_TYPE': 'Memo Type',
            'ENCLOSURES': 'Enclosures',
            'ADDRESS_CONSISTENCY': 'Address Format'
        };
        return names[fieldName] || fieldName;
    }

    // Highlight field in editor by selecting the line
    function highlightFieldInEditor(fieldName) {
        if (!editor) return;

        const text = editor.value;
        const pattern = new RegExp(`^${fieldName}\\s*=`, 'm');
        const match = text.match(pattern);

        if (match) {
            const startIndex = text.indexOf(match[0]);
            const lineEnd = text.indexOf('\n', startIndex);
            const endIndex = lineEnd === -1 ? text.length : lineEnd;

            editor.focus();
            editor.setSelectionRange(startIndex, endIndex);

            // Scroll to selection
            const lineNumber = text.substring(0, startIndex).split('\n').length;
            const lineHeight = parseInt(getComputedStyle(editor).lineHeight) || 20;
            editor.scrollTop = (lineNumber - 3) * lineHeight;
        }
    }

    // Utility: escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Utility: truncate string
    function truncate(str, maxLength) {
        if (!str) return '';
        if (str.length <= maxLength) return str;
        return str.substring(0, maxLength) + '...';
    }

    // Expose for external use
    window.textEditorValidation = {
        validate: validateText
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
