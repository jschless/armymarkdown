/**
 * Shared Validation Rules for Army Memo Maker
 *
 * Used by both form-validation.js and text-editor-validation.js
 * Rules based on AR 25-50 formatting requirements.
 */

window.MemoValidationRules = (function () {
    'use strict';

    // Valid ranks (abbreviations)
    const VALID_RANKS = [
    // Enlisted
        'PVT', 'PV2', 'PFC', 'SPC', 'CPL', 'SGT', 'SSG', 'SFC', 'MSG', '1SG', 'SGM', 'CSM', 'SMA',
        // Warrant Officers
        'WO1', 'CW2', 'CW3', 'CW4', 'CW5',
        // Officers
        '2LT', '1LT', 'CPT', 'MAJ', 'LTC', 'COL', 'BG', 'MG', 'LTG', 'GEN', 'GA',
        // Civilians
        'MR', 'MRS', 'MS', 'DR'
    ];

    // Valid branches
    const VALID_BRANCHES = [
        'AD', 'AG', 'AR', 'AV', 'CA', 'CE', 'CM', 'CY', 'EN', 'FA', 'FI', 'IN',
        'JA', 'MC', 'MI', 'MP', 'MS', 'OD', 'QM', 'SC', 'SF', 'TC', 'USA'
    ];

    // US States and territories
    const VALID_STATES = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA',
        'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT',
        'VA', 'WA', 'WV', 'WI', 'WY', 'DC', 'PR', 'VI', 'GU', 'AS', 'MP',
        // APO/FPO
        'AE', 'AP', 'AA'
    ];

    // Valid memo types
    const VALID_MEMO_TYPES = [
        'MEMORANDUM FOR RECORD',
        'MEMORANDUM FOR',
        'MEMORANDUM THRU',
        'MEMORANDUM OF UNDERSTANDING',
        'MEMORANDUM OF AGREEMENT',
        'MEMORANDUM OF INSTRUCTION'
    ];

    // Validation rules for header fields
    const RULES = {
        DATE: {
            validate: function (value) {
                if (!value) return null;
                const pattern = /^\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$/i;
                if (!pattern.test(value)) {
                    return {
                        message: 'Date should be in format "DD Month YYYY" (e.g., "15 January 2025")',
                        severity: 'error'
                    };
                }
                return null;
            }
        },

        OFFICE_SYMBOL: {
            validate: function (value) {
                if (!value) return null;
                const pattern = /^[A-Z]{2,5}(-[A-Z0-9]{1,4})*$/i;
                if (!pattern.test(value)) {
                    return {
                        message: 'Office symbol should follow format like "ATZB-CD-E"',
                        severity: 'warning'
                    };
                }
                return null;
            }
        },

        RANK: {
            validate: function (value) {
                if (!value) return null;
                if (!VALID_RANKS.includes(value.toUpperCase())) {
                    return {
                        message: 'Rank should be a standard Army abbreviation (e.g., CPT, SGT, MAJ)',
                        severity: 'warning'
                    };
                }
                return null;
            }
        },

        BRANCH: {
            validate: function (value) {
                if (!value) return null;
                if (!VALID_BRANCHES.includes(value.toUpperCase())) {
                    return {
                        message: 'Branch should be a standard Army abbreviation (e.g., IN, EN, MI)',
                        severity: 'warning'
                    };
                }
                return null;
            }
        },

        SUBJECT: {
            validate: function (value) {
                if (!value) return null;

                // Check length
                if (value.length > 150) {
                    return {
                        message: `Subject should be under 150 characters (currently ${value.length})`,
                        severity: 'warning'
                    };
                }

                // Check for period at end (AR 25-50: subject lines don't end with a period)
                if (value.trim().endsWith('.')) {
                    return {
                        message: 'Subject line should not end with a period (per AR 25-50)',
                        severity: 'warning'
                    };
                }

                // Check capitalization - first letter should be capital
                if (value.length > 0 && value[0] !== value[0].toUpperCase()) {
                    return {
                        message: 'Subject should start with a capital letter',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        AUTHOR: {
            validate: function (value) {
                if (!value) return null;

                // Check for middle initial pattern: "First M. Last" or "First Middle Last"
                const hasMiddleInitial = /^[A-Z][a-z]+\s+[A-Z]\.?\s+[A-Z][a-z]+/.test(value);
                const hasMiddleName = /^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+/.test(value);

                if (!hasMiddleInitial && !hasMiddleName) {
                    const hasTwoParts = /^[A-Z][a-z]+\s+[A-Z][a-z]+$/.test(value);
                    if (hasTwoParts) {
                        return {
                            message: 'Consider adding middle initial (e.g., "John A. Smith")',
                            severity: 'warning'
                        };
                    }
                }

                // Check if name appears to be all caps
                if (value === value.toUpperCase() && value.length > 3) {
                    return {
                        message: 'Enter name in mixed case (e.g., "John A. Smith") - it will be capitalized automatically',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        ORGANIZATION_NAME: {
            validate: function (value) {
                if (!value) return null;

                // Check if starts with capital
                if (value.length > 0 && /^[a-z]/.test(value)) {
                    return {
                        message: 'Organization name should start with a capital letter',
                        severity: 'warning'
                    };
                }

                // Check minimum length
                if (value.length < 5) {
                    return {
                        message: 'Organization name seems too short',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        ORGANIZATION_STREET_ADDRESS: {
            validate: function (value) {
                if (!value) return null;

                // Check for basic street address pattern
                const hasNumber = /\d+/.test(value);
                if (!hasNumber) {
                    return {
                        message: 'Street address should include a building/street number',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        ORGANIZATION_CITY_STATE_ZIP: {
            validate: function (value) {
                if (!value) return null;

                // Pattern: City, ST XXXXX or City, ST XXXXX-XXXX
                const pattern = /^[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(-\d{4})?$/;
                const loosePattern = /^.+,\s*[A-Za-z]{2}\s+\d{5}/;

                if (!loosePattern.test(value)) {
                    return {
                        message: 'Format should be "City, ST XXXXX" (e.g., "Fort Liberty, NC 28310")',
                        severity: 'warning'
                    };
                }

                // Extract state abbreviation and validate
                const stateMatch = value.match(/,\s*([A-Za-z]{2})\s+\d{5}/);
                if (stateMatch) {
                    const state = stateMatch[1].toUpperCase();
                    if (!VALID_STATES.includes(state)) {
                        return {
                            message: `"${stateMatch[1]}" doesn't appear to be a valid state abbreviation`,
                            severity: 'warning'
                        };
                    }
                }

                // Check for proper capitalization
                if (!pattern.test(value) && loosePattern.test(value)) {
                    return {
                        message: 'State abbreviation should be uppercase (e.g., "NC" not "nc")',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        TITLE: {
            validate: function (value) {
                if (!value) return null;

                // Check capitalization
                if (value.length > 0 && /^[a-z]/.test(value)) {
                    return {
                        message: 'Title should start with a capital letter',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        SUSPENSE: {
            validate: function (value) {
                if (!value) return null;

                const pattern = /^\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$/i;
                if (!pattern.test(value)) {
                    return {
                        message: 'Suspense date should be in format "DD Month YYYY"',
                        severity: 'error'
                    };
                }
                return null;
            }
        },

        MEMO_TYPE: {
            validate: function (value) {
                if (!value) return null;

                const upperValue = value.toUpperCase().trim();

                // Check if it starts with a valid memo type
                const isValid = VALID_MEMO_TYPES.some(type => upperValue.startsWith(type));

                if (!isValid) {
                    return {
                        message: 'Memo type should be "MEMORANDUM FOR", "MEMORANDUM FOR RECORD", "MEMORANDUM THRU", etc.',
                        severity: 'warning'
                    };
                }

                // Check if MEMORANDUM FOR has an addressee (not just "MEMORANDUM FOR")
                if (upperValue === 'MEMORANDUM FOR') {
                    return {
                        message: 'MEMORANDUM FOR should include an addressee',
                        severity: 'warning'
                    };
                }

                return null;
            }
        },

        ENCLOSURES: {
            validate: function (value) {
                if (!value) return null;

                const lines = value.split('\n').filter(l => l.trim());

                // Check singular vs plural
                if (lines.length === 1) {
                    // Single enclosure should not have "1." prefix
                    if (/^\s*1\./.test(lines[0])) {
                        return {
                            message: 'Single enclosure should not be numbered (use "Encl" not "Encl 1" or "1.")',
                            severity: 'warning'
                        };
                    }
                }

                // Check sequential numbering for multiple enclosures
                if (lines.length > 1) {
                    for (let i = 0; i < lines.length; i++) {
                        const expectedNum = i + 1;
                        const hasCorrectNumber = new RegExp(`^\\s*${expectedNum}[.)]`).test(lines[i]);
                        if (!hasCorrectNumber && !/^\s*-/.test(lines[i])) {
                            return {
                                message: 'Enclosures should be numbered sequentially (1, 2, 3...)',
                                severity: 'warning'
                            };
                        }
                    }
                }

                return null;
            }
        }
    };

    // Required fields
    const REQUIRED_FIELDS = [
        'ORGANIZATION_NAME',
        'ORGANIZATION_STREET_ADDRESS',
        'ORGANIZATION_CITY_STATE_ZIP',
        'OFFICE_SYMBOL',
        'DATE',
        'SUBJECT',
        'AUTHOR',
        'RANK',
        'BRANCH'
    ];

    /**
   * Validate memo body text for AR 25-50 compliance
   * @param {string} bodyText - The memo body text (after ---)
   * @returns {array} - Array of { message, severity, location } objects
   */
    function validateBodyText(bodyText) {
        const issues = [];
        if (!bodyText || !bodyText.trim()) return issues;

        const lines = bodyText.split('\n');
        const paragraphs = [];
        let currentPara = [];

        // Parse paragraphs
        for (const line of lines) {
            if (line.trim() === '') {
                if (currentPara.length > 0) {
                    paragraphs.push(currentPara.join('\n'));
                    currentPara = [];
                }
            } else {
                currentPara.push(line);
            }
        }
        if (currentPara.length > 0) {
            paragraphs.push(currentPara.join('\n'));
        }

        // Check paragraph numbering
        const totalParas = paragraphs.filter(p => p.trim().length > 0);

        // Rule: Don't number a single-paragraph memo
        if (totalParas.length === 1 && /^\s*1\./.test(totalParas[0])) {
            issues.push({
                message: 'Single-paragraph memos should not be numbered (per AR 25-50)',
                severity: 'warning',
                location: 'body'
            });
        }

        // Check subparagraph rules
        const subparagraphIssues = validateSubparagraphs(bodyText);
        issues.push(...subparagraphIssues);

        // Check for POC in last paragraph
        const pocIssues = validatePOCParagraph(paragraphs);
        issues.push(...pocIssues);

        // Check enclosure references in body
        const enclosureIssues = validateEnclosureReferences(bodyText);
        issues.push(...enclosureIssues);

        return issues;
    }

    /**
   * Validate subparagraph structure
   */
    function validateSubparagraphs(text) {
        const issues = [];

        // Check for lonely subparagraphs (a. without b., (1) without (2), etc.)
        // Pattern: if there's an "a." there should be a "b."
        if (/\ba\.\s/.test(text) && !/\bb\.\s/.test(text)) {
            issues.push({
                message: 'Subparagraph "a." requires at least "b." - subdivisions need minimum 2 items (per AR 25-50)',
                severity: 'warning',
                location: 'body'
            });
        }

        // Check for (1) without (2)
        if (/\(1\)\s/.test(text) && !/\(2\)\s/.test(text)) {
            issues.push({
                message: 'Subparagraph "(1)" requires at least "(2)" - subdivisions need minimum 2 items',
                severity: 'warning',
                location: 'body'
            });
        }

        // Check for (a) without (b)
        if (/\(a\)\s/i.test(text) && !/\(b\)\s/i.test(text)) {
            issues.push({
                message: 'Subparagraph "(a)" requires at least "(b)" - subdivisions need minimum 2 items',
                severity: 'warning',
                location: 'body'
            });
        }

        // Check for excessive subdivision (beyond third level)
        // Third level is (a), (b), etc. - anything deeper is not allowed
        if (/\(\(|\)\)/.test(text) || /\(i\)\s/i.test(text) || /\(ii\)\s/i.test(text)) {
            issues.push({
                message: 'Do not subdivide beyond the third level: 1. → a. → (1) → (a) (per AR 25-50)',
                severity: 'warning',
                location: 'body'
            });
        }

        return issues;
    }

    /**
   * Validate POC paragraph is last and properly formatted
   */
    function validatePOCParagraph(paragraphs) {
        const issues = [];
        if (paragraphs.length === 0) return issues;

        // Find POC mentions
        const pocPattern = /point of contact|POC|undersigned/i;
        let pocParaIndex = -1;

        for (let i = 0; i < paragraphs.length; i++) {
            if (pocPattern.test(paragraphs[i])) {
                pocParaIndex = i;
            }
        }

        // If POC found but not in last paragraph
        if (pocParaIndex !== -1 && pocParaIndex !== paragraphs.length - 1) {
            issues.push({
                message: 'Point of contact should be in the last paragraph (per AR 25-50)',
                severity: 'warning',
                location: 'body'
            });
        }

        // Check if POC paragraph has required info (phone, email)
        if (pocParaIndex !== -1) {
            const pocPara = paragraphs[pocParaIndex];

            // Check for phone number pattern
            const hasPhone = /\d{3}[-.)]\s*\d{3}[-.)]\s*\d{4}|DSN\s*\d+/i.test(pocPara);

            // Check for email pattern
            const hasEmail = /@/.test(pocPara) || /email/i.test(pocPara);

            if (!hasPhone && !hasEmail && !/undersigned/i.test(pocPara)) {
                issues.push({
                    message: 'POC paragraph should include phone number and/or email address',
                    severity: 'warning',
                    location: 'body'
                });
            }
        }

        return issues;
    }

    /**
   * Validate enclosure references match enclosure list
   */
    function validateEnclosureReferences(text) {
        const issues = [];

        // Find all enclosure references in body (Encl 1, Encl 2, etc.)
        const bodyRefs = text.match(/Encl(?:losure)?\s*(\d+)/gi) || [];
        const refNumbers = bodyRefs.map(ref => {
            const match = ref.match(/\d+/);
            return match ? parseInt(match[0]) : 0;
        }).filter(n => n > 0);

        // Check for gaps in enclosure numbering
        if (refNumbers.length > 0) {
            const maxRef = Math.max(...refNumbers);
            for (let i = 1; i <= maxRef; i++) {
                if (!refNumbers.includes(i)) {
                    issues.push({
                        message: `Enclosure ${i} is not referenced but Enclosure ${maxRef} is - number enclosures in order of appearance`,
                        severity: 'warning',
                        location: 'body'
                    });
                    break;
                }
            }
        }

        return issues;
    }

    /**
   * Check address consistency (all caps or mixed case, not both)
   */
    function validateAddressConsistency(fields) {
        const issues = [];

        const addressFields = [
            fields.ORGANIZATION_NAME,
            fields.ORGANIZATION_STREET_ADDRESS,
            fields.ORGANIZATION_CITY_STATE_ZIP
        ].filter(f => f && f.trim());

        if (addressFields.length < 2) return issues;

        // Check if some are all caps and some are mixed
        const allCapsFields = addressFields.filter(f => f === f.toUpperCase());
        const mixedCaseFields = addressFields.filter(f => f !== f.toUpperCase() && f !== f.toLowerCase());

        if (allCapsFields.length > 0 && mixedCaseFields.length > 0) {
            issues.push({
                field: 'ADDRESS_CONSISTENCY',
                message: 'Address lines should be consistently ALL CAPS or Mixed Case, not both (per AR 25-50)',
                severity: 'warning'
            });
        }

        return issues;
    }

    // Public API
    return {
        RULES: RULES,
        REQUIRED_FIELDS: REQUIRED_FIELDS,
        VALID_RANKS: VALID_RANKS,
        VALID_BRANCHES: VALID_BRANCHES,
        VALID_STATES: VALID_STATES,
        VALID_MEMO_TYPES: VALID_MEMO_TYPES,

        /**
     * Validate a single field
     */
        validateField: function (fieldName, value) {
            const trimmedValue = (value || '').trim();

            // Check required
            if (REQUIRED_FIELDS.includes(fieldName) && !trimmedValue) {
                return {
                    message: 'This field is required',
                    severity: 'error'
                };
            }

            // Check specific rules
            if (RULES[fieldName] && trimmedValue) {
                return RULES[fieldName].validate(trimmedValue);
            }

            return null;
        },

        /**
     * Validate all fields in a data object
     */
        validateAll: function (data) {
            const results = {};
            const allFields = [...new Set([...Object.keys(RULES), ...REQUIRED_FIELDS])];

            allFields.forEach(function (fieldName) {
                const result = this.validateField(fieldName, data[fieldName]);
                if (result) {
                    results[fieldName] = result;
                }
            }, this);

            // Check address consistency
            const addressIssues = validateAddressConsistency(data);
            addressIssues.forEach(function (issue) {
                results[issue.field] = { message: issue.message, severity: issue.severity };
            });

            return results;
        },

        /**
     * Validate body text
     */
        validateBodyText: validateBodyText,

        /**
     * Parse AMD format text into field object
     */
        parseAmdText: function (text) {
            const fields = {};
            const lines = text.split('\n');
            let inBody = false;
            const bodyLines = [];

            for (const line of lines) {
                // Check for body separator
                if (line.trim() === '---') {
                    inBody = true;
                    continue;
                }

                if (inBody) {
                    bodyLines.push(line);
                } else {
                    // Parse field assignment
                    const match = line.match(/^([A-Z_]+)\s*=\s*(.*)$/);
                    if (match) {
                        fields[match[1]] = match[2].trim();
                    }
                }
            }

            // Store body text for validation
            fields._BODY_TEXT = bodyLines.join('\n');

            return fields;
        },

        /**
     * Full validation including body text
     */
        validateComplete: function (text) {
            const fields = this.parseAmdText(text);
            const fieldIssues = this.validateAll(fields);
            const bodyIssues = validateBodyText(fields._BODY_TEXT || '');

            return {
                fieldIssues: fieldIssues,
                bodyIssues: bodyIssues,
                hasErrors: Object.values(fieldIssues).some(i => i.severity === 'error') ||
                   bodyIssues.some(i => i.severity === 'error'),
                hasWarnings: Object.values(fieldIssues).some(i => i.severity === 'warning') ||
                     bodyIssues.some(i => i.severity === 'warning')
            };
        }
    };
})();
