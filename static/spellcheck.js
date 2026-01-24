/* global Typo */
/**
 * Spellcheck service using Typo.js with military dictionary
 *
 * Provides client-side spellchecking for Army memos with a custom
 * military dictionary to whitelist common Army terms, acronyms, and ranks.
 */
(function() {
    'use strict';

    let typo = null;
    const militaryTerms = new Set();
    let initialized = false;
    let initializing = false;

    /**
   * Initialize Typo.js with dictionaries
   * @returns {Promise<void>}
   */
    async function init() {
        if (initialized || initializing) return;
        initializing = true;

        try {
            // Check if Typo is available
            if (typeof Typo === 'undefined') {
                console.warn('Typo.js not loaded, spellcheck disabled');
                return;
            }

            // Load main dictionary files
            const [affData, dicData] = await Promise.all([
                fetch('/static/dictionaries/en_US.aff').then(r => {
                    if (!r.ok) throw new Error('Failed to load en_US.aff');
                    return r.text();
                }),
                fetch('/static/dictionaries/en_US.dic').then(r => {
                    if (!r.ok) throw new Error('Failed to load en_US.dic');
                    return r.text();
                })
            ]);

            typo = new Typo('en_US', affData, dicData);

            // Load military terms dictionary
            try {
                const militaryData = await fetch('/static/dictionaries/military-terms.txt').then(r => {
                    if (!r.ok) throw new Error('Failed to load military-terms.txt');
                    return r.text();
                });

                militaryData.split('\n').forEach(line => {
                    line = line.trim();
                    // Skip empty lines and comments
                    if (line && !line.startsWith('#')) {
                        // Handle multiple terms on same line (space-separated)
                        line.split(/\s+/).forEach(term => {
                            if (term) {
                                militaryTerms.add(term.toUpperCase());
                            }
                        });
                    }
                });
            } catch (err) {
                console.warn('Military dictionary not loaded:', err.message);
            }

            initialized = true;
            console.log('Spellcheck initialized with', militaryTerms.size, 'military terms');
        } catch (err) {
            console.error('Failed to initialize spellcheck:', err);
        } finally {
            initializing = false;
        }
    }

    /**
   * Check if a word is valid (correctly spelled or in military dictionary)
   * @param {string} word - The word to check
   * @returns {boolean} - True if word is valid
   */
    function isValidWord(word) {
        if (!typo) return true; // Fail open if not initialized

        // Skip very short words (1 character)
        if (word.length < 2) return true;

        // Skip numbers and words with numbers (e.g., M16, AR-670-1)
        if (/\d/.test(word)) return true;

        // Skip words that are all punctuation or special chars
        if (!/[a-zA-Z]/.test(word)) return true;

        // Check military dictionary first (case-insensitive)
        if (militaryTerms.has(word.toUpperCase())) return true;

        // Check main dictionary
        return typo.check(word);
    }

    /**
   * Get spelling suggestions for a misspelled word
   * @param {string} word - The misspelled word
   * @returns {string[]} - Array of suggestions (max 5)
   */
    function suggest(word) {
        if (!typo) return [];
        return typo.suggest(word).slice(0, 5);
    }

    /**
   * Check text and return array of misspellings
   * @param {string} text - The text to check
   * @returns {Array<{word: string, suggestions: string[]}>} - Array of misspelling objects
   */
    function checkText(text) {
        if (!initialized || !text) return [];

        const misspellings = [];

        // Extract words - keep apostrophes for contractions, handle hyphenated words
        const words = text.match(/[a-zA-Z][a-zA-Z'-]*[a-zA-Z]|[a-zA-Z]/g) || [];
        const seen = new Set();

        for (const word of words) {
            // Skip already checked words (case-insensitive)
            const lowerWord = word.toLowerCase();
            if (seen.has(lowerWord)) continue;
            seen.add(lowerWord);

            // Clean word - remove leading/trailing apostrophes and hyphens
            const cleanWord = word.replace(/^['-]+|['-]+$/g, '');
            if (cleanWord.length < 2) continue;

            // For hyphenated words, check each part separately
            if (cleanWord.includes('-')) {
                const parts = cleanWord.split('-');
                let allPartsValid = true;
                for (const part of parts) {
                    if (part.length >= 2 && !isValidWord(part)) {
                        allPartsValid = false;
                        break;
                    }
                }
                if (allPartsValid) continue;
            }

            if (!isValidWord(cleanWord)) {
                misspellings.push({
                    word: cleanWord,
                    suggestions: suggest(cleanWord)
                });
            }
        }

        return misspellings;
    }

    /**
   * Add a word to the military terms dictionary (session only)
   * @param {string} word - The word to add
   */
    function addWord(word) {
        if (word && word.length >= 2) {
            militaryTerms.add(word.toUpperCase());
        }
    }

    /**
   * Check if spellcheck is ready to use
   * @returns {boolean}
   */
    function isReady() {
        return initialized;
    }

    // Export public API
    window.Spellcheck = {
        init: init,
        checkText: checkText,
        isValidWord: isValidWord,
        suggest: suggest,
        addWord: addWord,
        isReady: isReady
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
