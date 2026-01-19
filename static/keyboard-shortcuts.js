/* global MouseEvent, setTimeout */
// Keyboard shortcuts for memo editor
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.isEnabled = true;
        this.init();
    }

    init() {
        // Register keyboard shortcuts
        this.addShortcut('Ctrl+S', 'Save Progress', () => this.handleSave());
        this.addShortcut('Ctrl+Enter', 'Generate PDF', () => this.handleGenerate());
        this.addShortcut('Ctrl+O', 'Open Document', () => this.handleOpen());
        this.addShortcut('Ctrl+N', 'New Document', () => this.handleNew());
        this.addShortcut('Ctrl+/', 'Show Shortcuts', () => this.showShortcutsHelp());

        // Mac equivalents
        this.addShortcut('Cmd+S', 'Save Progress', () => this.handleSave());
        this.addShortcut('Cmd+Enter', 'Generate PDF', () => this.handleGenerate());
        this.addShortcut('Cmd+O', 'Open Document', () => this.handleOpen());
        this.addShortcut('Cmd+N', 'New Document', () => this.handleNew());
        this.addShortcut('Cmd+/', 'Show Shortcuts', () => this.showShortcutsHelp());

        // Attach event listeners
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // Create help overlay
        this.createHelpOverlay();

        console.log('Keyboard shortcuts initialized');
        console.log('Press Ctrl+/ (or Cmd+/) to view all shortcuts');
    }

    addShortcut(keys, description, callback) {
        this.shortcuts.set(keys.toLowerCase(), {
            description,
            callback,
            keys
        });
    }

    handleKeyDown(event) {
        if (!this.isEnabled) return;

        // Don't trigger shortcuts when typing in input fields (except for save)
        const isInInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName);
        const isContentEditable = event.target.contentEditable === 'true';

        // Build the key combination string
        let combo = '';
        if (event.ctrlKey) combo += 'ctrl+';
        if (event.metaKey) combo += 'cmd+';
        if (event.altKey) combo += 'alt+';
        if (event.shiftKey) combo += 'shift+';

        // Add the main key
        if (event.key === 'Enter') {
            combo += 'enter';
        } else if (event.key === '/') {
            combo += '/';
        } else {
            combo += event.key.toLowerCase();
        }

        // Check if this combination exists
        const shortcut = this.shortcuts.get(combo);
        if (shortcut) {
            // Always allow save shortcuts and help shortcuts
            if (combo.includes('s') || combo.includes('/')) {
                event.preventDefault();
                shortcut.callback();
                return;
            }

            // For other shortcuts, only trigger if not in input field
            if (!isInInput && !isContentEditable) {
                event.preventDefault();
                shortcut.callback();
            }
        }
    }

    handleSave() {
        const saveButton = document.getElementById('save-progress');
        if (saveButton) {
            // Show visual feedback
            this.showShortcutFeedback('Saving...', 'info');
            saveButton.click();
        } else {
            this.showShortcutFeedback('Save unavailable (login required)', 'warning');
        }
    }

    handleGenerate() {
        const generateButton = document.getElementById('start-bg-job');
        if (generateButton) {
            this.showShortcutFeedback('Generating PDF...', 'info');
            generateButton.click();
        } else {
            this.showShortcutFeedback('Generate button not found', 'error');
        }
    }

    handleOpen() {
        const linkSelector = document.getElementById('linkSelector');
        if (linkSelector) {
            // Focus on the dropdown and expand it
            linkSelector.focus();

            // Trigger a click to open the dropdown
            const clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true
            });
            linkSelector.dispatchEvent(clickEvent);

            this.showShortcutFeedback('Document selector opened', 'success');
        } else {
            this.showShortcutFeedback('Document selector not available', 'warning');
        }
    }

    handleNew() {
        // Clear the main editor content
        const editor = document.getElementById('editor');
        const memoText = document.getElementById('MEMO_TEXT');

        if (editor) {
            editor.value = '';
            editor.focus();
            this.showShortcutFeedback('Text editor cleared', 'success');
        } else if (memoText) {
            memoText.value = '';
            memoText.focus();
            this.showShortcutFeedback('Form content cleared', 'success');
        } else {
            // Navigate to index page for new document
            window.location.href = '/';
        }
    }

    showShortcutsHelp() {
        const helpOverlay = document.getElementById('shortcuts-help-overlay');
        if (helpOverlay) {
            helpOverlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    hideShortcutsHelp() {
        const helpOverlay = document.getElementById('shortcuts-help-overlay');
        if (helpOverlay) {
            helpOverlay.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    createHelpOverlay() {
        // Create help overlay HTML
        const overlay = document.createElement('div');
        overlay.id = 'shortcuts-help-overlay';
        overlay.className = 'shortcuts-help-overlay';

        overlay.innerHTML = `
            <div class="shortcuts-help-modal">
                <div class="shortcuts-help-header">
                    <h2>Keyboard Shortcuts</h2>
                    <button class="shortcuts-help-close" onclick="window.keyboardShortcuts.hideShortcutsHelp()">&times;</button>
                </div>
                <div class="shortcuts-help-content">
                    <div class="shortcuts-help-section">
                        <h3>Document Actions</h3>
                        <div class="shortcut-item">
                            <span class="shortcut-keys">Ctrl+S / ⌘+S</span>
                            <span class="shortcut-desc">Save Progress</span>
                        </div>
                        <div class="shortcut-item">
                            <span class="shortcut-keys">Ctrl+Enter / ⌘+Enter</span>
                            <span class="shortcut-desc">Generate PDF</span>
                        </div>
                        <div class="shortcut-item">
                            <span class="shortcut-keys">Ctrl+O / ⌘+O</span>
                            <span class="shortcut-desc">Open Document</span>
                        </div>
                        <div class="shortcut-item">
                            <span class="shortcut-keys">Ctrl+N / ⌘+N</span>
                            <span class="shortcut-desc">New Document</span>
                        </div>
                    </div>
                    <div class="shortcuts-help-section">
                        <h3>Help</h3>
                        <div class="shortcut-item">
                            <span class="shortcut-keys">Ctrl+/ / ⌘+/</span>
                            <span class="shortcut-desc">Show This Help</span>
                        </div>
                        <div class="shortcut-item">
                            <span class="shortcut-keys">Esc</span>
                            <span class="shortcut-desc">Close Help</span>
                        </div>
                    </div>
                </div>
                <div class="shortcuts-help-footer">
                    <p>Shortcuts work when not typing in form fields (except save)</p>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Add escape key handler for help overlay
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && overlay.style.display === 'flex') {
                this.hideShortcutsHelp();
            }
        });

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.hideShortcutsHelp();
            }
        });
    }

    showShortcutFeedback(message, type = 'info') {
        // Create or update feedback element
        let feedback = document.getElementById('shortcut-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.id = 'shortcut-feedback';
            feedback.className = 'shortcut-feedback';
            document.body.appendChild(feedback);
        }

        feedback.className = `shortcut-feedback shortcut-feedback-${type}`;
        feedback.textContent = message;
        feedback.style.display = 'block';

        // Auto-hide after 2 seconds
        setTimeout(() => {
            feedback.style.display = 'none';
        }, 2000);
    }

    enable() {
        this.isEnabled = true;
    }

    disable() {
        this.isEnabled = false;
    }
}

// Initialize keyboard shortcuts when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.keyboardShortcuts = new KeyboardShortcuts();
});
