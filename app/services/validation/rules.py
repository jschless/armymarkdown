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
        id="SUBJECT_002",
        name="Subject Line Length",
        description="Subject line should not exceed 150 characters",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-3",
        check_function="check_subject_length",
    ),
    ValidationRule(
        id="BODY_001",
        name="Paragraph Numbering",
        description="Body paragraphs should be numbered",
        severity=Severity.WARNING,
        ar_reference="AR 25-50, para 2-4",
        check_function="check_paragraph_numbering",
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
