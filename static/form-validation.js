/* global clearTimeout, setTimeout, document, window */
/**
 * Real-time Form Validation for Army Memo Form
 *
 * Provides advisory validation hints as users fill out the form.
 * Does NOT block form submission - purely informational.
 *
 * Uses shared validation rules from validation-rules.js
 */

(function () {
    'use strict';

    // Wait for validation rules to load
    function initWhenReady() {
        if (typeof window.MemoValidationRules === 'undefined') {
            // Retry after a short delay
            setTimeout(initWhenReady, 100);
            return;
        }
        init();
    }

    const Rules = window.MemoValidationRules || {};

    // Debounce timer
    let debounceTimer = null;
    const DEBOUNCE_DELAY = 500;

    // Get all validatable fields
    function getValidatableFields() {
        if (!Rules.RULES || !Rules.REQUIRED_FIELDS) return [];
        return [...new Set([...Object.keys(Rules.RULES), ...Rules.REQUIRED_FIELDS])];
    }

    // Initialize validation
    function init() {
        const form = document.getElementById('memo');
        if (!form) return;

        // Check if this is the form page (has SUBJECT field) not text editor
        if (!document.getElementById('SUBJECT')) return;

        // Add validation hint containers after each validatable field
        addValidationHints();

        // Attach event listeners
        attachEventListeners();
    }

    // Add validation hint spans after form fields
    function addValidationHints() {
        const fields = getValidatableFields();

        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && !document.getElementById(`${fieldId}-hint`)) {
                const hint = document.createElement('span');
                hint.id = `${fieldId}-hint`;
                hint.className = 'validation-hint';
                hint.setAttribute('role', 'alert');
                hint.setAttribute('aria-live', 'polite');
                field.parentNode.insertBefore(hint, field.nextSibling);
            }
        });
    }

    // Attach event listeners to form fields
    function attachEventListeners() {
        const fields = getValidatableFields();

        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                // Validate on blur
                field.addEventListener('blur', () => validateField(fieldId));

                // Validate on input (debounced)
                field.addEventListener('input', () => {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => validateField(fieldId), DEBOUNCE_DELAY);
                });
            }
        });
    }

    // Validate a single field
    function validateField(fieldId) {
        const field = document.getElementById(fieldId);
        const hint = document.getElementById(`${fieldId}-hint`);
        if (!field || !hint) return;

        const value = field.value.trim();
        const result = Rules.validateField(fieldId, value);

        // Update UI
        updateFieldStatus(field, hint, result);
    }

    // Update field visual status
    function updateFieldStatus(field, hint, result) {
    // Remove all status classes
        field.classList.remove('field-valid', 'field-warning', 'field-error');
        hint.classList.remove('hint-warning', 'hint-error');

        if (result) {
            hint.textContent = result.message;
            hint.style.display = 'block';

            if (result.severity === 'error') {
                field.classList.add('field-error');
                hint.classList.add('hint-error');
            } else if (result.severity === 'warning') {
                field.classList.add('field-warning');
                hint.classList.add('hint-warning');
            }
        } else {
            hint.textContent = '';
            hint.style.display = 'none';

            // If field has value and passes validation, mark as valid
            if (field.value.trim()) {
                field.classList.add('field-valid');
            }
        }
    }

    // Validate all fields (can be called before submission)
    function validateAllFields() {
        const fields = getValidatableFields();

        let hasErrors = false;
        fields.forEach(fieldId => {
            validateField(fieldId);
            const hint = document.getElementById(`${fieldId}-hint`);
            if (hint && hint.classList.contains('hint-error')) {
                hasErrors = true;
            }
        });

        return !hasErrors;
    }

    // Expose validation function globally for optional use
    window.formValidation = {
        validateField,
        validateAllFields
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWhenReady);
    } else {
        initWhenReady();
    }
})();
