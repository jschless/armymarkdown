/* global clearTimeout, clearInterval, setInterval, setTimeout */
// Auto-save functionality for memo drafts
class AutoSave {
    constructor(options = {}) {
        this.interval = options.interval || 30000; // 30 seconds default
        this.isAuthenticated = options.isAuthenticated || false;
        this.debounceDelay = options.debounceDelay || 3000; // 3 seconds after user stops typing

        this.timer = null;
        this.debounceTimer = null;
        this.lastSaveTime = null;
        this.isEnabled = false;
        this.isDirty = false;

        this.init();
    }

    init() {
        if (!this.isAuthenticated) {
            return; // Only enable auto-save for authenticated users
        }

        this.isEnabled = true;
        this.createStatusIndicator();
        this.attachEventListeners();
        this.startAutoSave();

        console.log('Auto-save enabled: saves every', this.interval / 1000, 'seconds');
    }

    createStatusIndicator() {
        // Create auto-save status indicator
        const indicator = document.createElement('div');
        indicator.id = 'auto-save-status';
        indicator.className = 'auto-save-status';
        indicator.innerHTML = '<span class="auto-save-text">Auto-save enabled</span>';

        // Find the save button to position indicator near it
        const saveButton = document.getElementById('save-progress');
        if (saveButton) {
            saveButton.parentNode.insertBefore(indicator, saveButton.nextSibling);
        } else {
            // Fallback: add to form
            const form = document.getElementById('memo');
            if (form) {
                form.appendChild(indicator);
            }
        }

        this.statusElement = indicator;
    }

    attachEventListeners() {
        // Listen for changes in form fields
        const form = document.getElementById('memo');
        if (!form) return;

        // Get all input and textarea elements
        const inputs = form.querySelectorAll('input, textarea');

        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.markDirty();
                this.debounceAutoSave();
            });

            input.addEventListener('change', () => {
                this.markDirty();
                this.debounceAutoSave();
            });
        });

        // Listen for window unload to save before leaving
        window.addEventListener('beforeunload', () => {
            if (this.isDirty) {
                this.performAutoSave();
            }
        });
    }

    markDirty() {
        this.isDirty = true;
    }

    debounceAutoSave() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.debounceTimer = setTimeout(() => {
            if (this.isDirty) {
                this.performAutoSave();
            }
        }, this.debounceDelay);
    }

    startAutoSave() {
        if (this.timer) {
            clearInterval(this.timer);
        }

        this.timer = setInterval(() => {
            if (this.isDirty) {
                this.performAutoSave();
            }
        }, this.interval);
    }

    async performAutoSave() {
        if (!this.isEnabled || !this.isDirty) {
            return;
        }

        try {
            this.updateStatus('saving', 'Auto-saving...');

            const form = document.getElementById('memo');
            if (!form) {
                throw new Error('Form not found');
            }

            const formData = new FormData(form);

            const response = await fetch('/auto_save', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.lastSaveTime = new Date(result.timestamp * 1000);

                // Handle different auto-save actions
                if (result.action === 'skipped') {
                    // Document content is identical, no need to save
                    this.updateStatus('idle', 'No changes to save');

                    // Hide status after 2 seconds since it's just informational
                    setTimeout(() => {
                        this.updateStatus('idle', 'Auto-save enabled');
                    }, 2000);
                } else if (result.action === 'saved') {
                    // Document was actually saved
                    this.isDirty = false;
                    const message = result.removed_oldest ?
                        `Draft saved (removed oldest) at ${this.formatTime(this.lastSaveTime)}` :
                        `Draft saved at ${this.formatTime(this.lastSaveTime)}`;

                    this.updateStatus('saved', message);

                    // Hide status after 3 seconds
                    setTimeout(() => {
                        this.updateStatus('idle', 'Auto-save enabled');
                    }, 3000);
                } else {
                    // Generic success case
                    this.isDirty = false;
                    this.updateStatus('saved', result.message || 'Draft auto-saved');

                    setTimeout(() => {
                        this.updateStatus('idle', 'Auto-save enabled');
                    }, 3000);
                }

            } else {
                this.updateStatus('error', `Auto-save failed: ${result.error}`);
                console.error('Auto-save failed:', result.error);
            }

        } catch (error) {
            this.updateStatus('error', 'Auto-save failed');
            console.error('Auto-save error:', error);
        }
    }

    updateStatus(state, message) {
        if (!this.statusElement) return;

        const textElement = this.statusElement.querySelector('.auto-save-text');
        if (textElement) {
            textElement.textContent = message;
        }

        // Update CSS class for styling
        this.statusElement.className = `auto-save-status auto-save-${state}`;
    }

    formatTime(date) {
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    disable() {
        this.isEnabled = false;
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = null;
        }

        if (this.statusElement) {
            this.statusElement.style.display = 'none';
        }
    }

    enable() {
        if (this.isAuthenticated) {
            this.isEnabled = true;
            this.startAutoSave();
            if (this.statusElement) {
                this.statusElement.style.display = 'block';
                this.updateStatus('idle', 'Auto-save enabled');
            }
        }
    }
}

// Initialize auto-save when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated by looking for the save button
    const isAuthenticated = document.getElementById('save-progress') !== null;

    if (isAuthenticated) {
        window.autoSave = new AutoSave({
            isAuthenticated: isAuthenticated,
            interval: 30000, // 30 seconds
            debounceDelay: 3000 // 3 seconds after user stops typing
        });
    }
});
