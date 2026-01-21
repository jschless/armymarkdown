"""
AR 25-50 Compliance Rules for Army Memorandums.

This module defines the validation rules based on Army Regulation 25-50
(Preparing and Managing Correspondence).

These rules are used by the PDF validation service to check compliance.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Must fix - document is non-compliant
    WARNING = "warning"  # Should fix - document is technically compliant but suboptimal
    INFO = "info"  # Informational - best practice suggestion


@dataclass
class ValidationRule:
    """Definition of a single validation rule."""

    id: str
    name: str
    description: str
    severity: Severity
    ar_reference: str  # AR 25-50 paragraph reference
    check_function: str  # Name of function to run check


# AR 25-50 Formatting Rules
AR_25_50_RULES = {
    # Font Requirements
    "font": {
        "required": "Arial",
        "acceptable": ["Arial", "Courier New"],
        "size": 12,
        "size_tolerance": 0,  # Points tolerance
    },
    # Margin Requirements (in inches)
    "margins": {
        "top": 1.0,
        "bottom": 1.0,
        "left": 1.0,
        "right": 1.0,
        "tolerance": 0.1,  # Inches tolerance
    },
    # Line Spacing
    "spacing": {
        "line": "single",
        "paragraph": 1,  # Number of blank lines between paragraphs
    },
    # Header Requirements
    "header": {
        "elements": [
            "department_line",  # "DEPARTMENT OF THE ARMY"
            "organization_name",
            "organization_address",
        ],
        "department_line": "DEPARTMENT OF THE ARMY",
    },
    # Date Format
    "date": {
        "format": "DD Month YYYY",
        "example": "15 January 2025",
    },
    # Subject Line
    "subject": {
        "max_length": 150,  # Characters
        "required": True,
    },
    # Signature Block
    "signature": {
        "elements": ["name", "rank", "branch", "title"],
        "caps": True,  # Name in all caps
    },
}

# Validation Rules with AR 25-50 References
VALIDATION_RULES = [
    ValidationRule(
        id="FONT_001",
        name="Font Type",
        description="Document must use Arial or Courier New font",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 1-17",
        check_function="check_font_type",
    ),
    ValidationRule(
        id="FONT_002",
        name="Font Size",
        description="Body text must be 12 point",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 1-17",
        check_function="check_font_size",
    ),
    ValidationRule(
        id="MARGIN_001",
        name="Page Margins",
        description="All margins must be 1 inch",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 1-17",
        check_function="check_margins",
    ),
    ValidationRule(
        id="HEADER_001",
        name="Department Line",
        description="First line must read 'DEPARTMENT OF THE ARMY'",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-2",
        check_function="check_department_line",
    ),
    ValidationRule(
        id="HEADER_002",
        name="Organization Header",
        description="Organization name and address must be present",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-2",
        check_function="check_organization_header",
    ),
    ValidationRule(
        id="DATE_001",
        name="Date Format",
        description="Date must be in format 'DD Month YYYY'",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_date_format",
    ),
    ValidationRule(
        id="SUBJECT_001",
        name="Subject Line Present",
        description="Memorandum must have a subject line",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_subject_present",
    ),
    ValidationRule(
        id="MEMO_FOR_001",
        name="MEMORANDUM FOR Capitalization",
        description="Address must be all uppercase OR title case, not mixed",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-3(5)",
        check_function="check_memo_for_capitalization",
    ),
    ValidationRule(
        id="SUBJECT_002",
        name="Subject Line Format",
        description="SUBJECT: must be uppercase; subject text should be 10 words or less",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_subject_format",
    ),
    ValidationRule(
        id="BODY_001",
        name="Paragraph Numbering",
        description="Body paragraphs should be numbered (1., 2., 3., etc.)",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-4",
        check_function="check_paragraph_numbering",
    ),
    ValidationRule(
        id="BODY_002",
        name="Subdivision Pairs",
        description="When subdividing, must have at least two sub-items (a AND b)",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-4",
        check_function="check_subdivision_pairs",
    ),
    ValidationRule(
        id="BODY_003",
        name="Line Continuation",
        description="Continuation lines should return to left margin (no hanging indent)",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-4",
        check_function="check_line_continuation",
    ),
    ValidationRule(
        id="BODY_004",
        name="Paragraph Indentation",
        description='Paragraphs must be indented per AR 25-50 (1/4" for a/b/c, 1/2" for (1)/(a))',
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-4",
        check_function="check_paragraph_indentation",
    ),
    ValidationRule(
        id="BODY_005",
        name="Maximum Subdivision Depth",
        description="Do not subdivide beyond level 4 ((a), (b), (c)) or indent beyond 1/2 inch",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-4",
        check_function="check_max_subdivision_depth",
    ),
    ValidationRule(
        id="SPACING_001",
        name="Vertical Spacing",
        description="Correct spacing between document sections (2 lines after office symbol, 4 before signature)",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-2",
        check_function="check_vertical_spacing",
    ),
    ValidationRule(
        id="SPACING_002",
        name="Sentence Spacing",
        description="Two spaces after periods/question marks, one space after other punctuation",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 1-17",
        check_function="check_sentence_spacing",
    ),
    ValidationRule(
        id="SPACING_003",
        name="Signature Block Placement",
        description="Signature block must not be alone on a page",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-5",
        check_function="check_signature_block_placement",
    ),
    ValidationRule(
        id="PAGE_001",
        name="Continuation Page Header",
        description='Continuation pages must have office symbol (1" from top) and subject',
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_continuation_page_header",
    ),
    ValidationRule(
        id="PAGE_002",
        name="Paragraph Page Division",
        description="Divided paragraphs must have at least 2 lines on each page",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_paragraph_page_division",
    ),
    ValidationRule(
        id="PAGE_003",
        name="Signature Block Content",
        description="Signature page must have at least 2 lines of last paragraph",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_signature_with_last_paragraph",
    ),
    ValidationRule(
        id="PAGE_004",
        name="Page Number Position",
        description="Page numbers should be centered, 1 inch from bottom",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_page_number_position",
    ),
    ValidationRule(
        id="STYLE_001",
        name="Army Term Capitalization",
        description="Capitalize Soldier, Family, and Civilian when referring to Army personnel",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, Appendix A",
        check_function="check_army_capitalization",
    ),
    ValidationRule(
        id="STYLE_002",
        name="Acronym Usage",
        description="Spell out acronyms on first use; avoid acronyms in subject line",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, Appendix A",
        check_function="check_acronym_usage",
    ),
    ValidationRule(
        id="SIG_001",
        name="Signature Block Present",
        description="Document must have a signature block",
        severity=Severity.ERROR,
        ar_reference="AR 25-50, para 2-5",
        check_function="check_signature_block",
    ),
    ValidationRule(
        id="SIG_002",
        name="Signature Name Case",
        description="Name in signature block should be in all capitals",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-5",
        check_function="check_signature_name_case",
    ),
    ValidationRule(
        id="ENCL_001",
        name="Enclosure Format",
        description="Enclosures should be properly formatted and numbered",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-6",
        check_function="check_enclosure_format",
    ),
]


def get_rules_by_severity(severity: Severity) -> list[ValidationRule]:
    """Get all rules with a specific severity level."""
    return [rule for rule in VALIDATION_RULES if rule.severity == severity]


def get_rule_by_id(rule_id: str) -> ValidationRule | None:
    """Get a specific rule by its ID."""
    for rule in VALIDATION_RULES:
        if rule.id == rule_id:
            return rule
    return None


def get_all_rules() -> list[ValidationRule]:
    """Get all validation rules."""
    return VALIDATION_RULES


def get_rule_config() -> dict[str, Any]:
    """Get the full rules configuration dictionary."""
    return AR_25_50_RULES
