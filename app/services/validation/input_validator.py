"""
Input validation for Army memorandums.

Validates memo content before LaTeX compilation to catch errors early
and provide helpful feedback to users.
"""

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import ClassVar


@dataclass
class ValidationResult:
    """Result of memo validation."""

    is_valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class MemoValidator:
    """Validates Army memorandum content before compilation."""

    # Valid Army ranks (abbreviations)
    VALID_RANKS: ClassVar[set[str]] = {
        # Enlisted
        "PVT",
        "PV2",
        "PFC",
        "SPC",
        "CPL",
        "SGT",
        "SSG",
        "SFC",
        "MSG",
        "1SG",
        "SGM",
        "CSM",
        "SMA",
        # Warrant Officers
        "WO1",
        "CW2",
        "CW3",
        "CW4",
        "CW5",
        # Officers
        "2LT",
        "1LT",
        "CPT",
        "MAJ",
        "LTC",
        "COL",
        "BG",
        "MG",
        "LTG",
        "GEN",
        "GA",
        # Civilians
        "MR",
        "MRS",
        "MS",
        "DR",
    }

    # Valid Army branches
    VALID_BRANCHES: ClassVar[set[str]] = {
        "AD",  # Air Defense
        "AG",  # Adjutant General
        "AR",  # Armor
        "AV",  # Aviation
        "CA",  # Civil Affairs
        "CE",  # Corps of Engineers
        "CM",  # Chemical
        "CY",  # Cyber
        "EN",  # Engineer
        "FA",  # Field Artillery
        "FI",  # Finance
        "IN",  # Infantry
        "JA",  # Judge Advocate
        "MC",  # Medical Corps
        "MI",  # Military Intelligence
        "MP",  # Military Police
        "MS",  # Medical Service
        "OD",  # Ordnance
        "QM",  # Quartermaster
        "SC",  # Signal Corps
        "SF",  # Special Forces
        "TC",  # Transportation Corps
        "USA",  # US Army (general)
    }

    # Date format pattern (DD Month YYYY or DD MONTH YYYY)
    DATE_PATTERN = re.compile(
        r"^\d{1,2}\s+(January|February|March|April|May|June|July|"
        r"August|September|October|November|December)\s+\d{4}$",
        re.IGNORECASE,
    )

    # Office symbol pattern (typically XXXX-XX-X format)
    OFFICE_SYMBOL_PATTERN = re.compile(r"^[A-Z]{2,5}(-[A-Z0-9]{1,4})*$", re.IGNORECASE)

    def __init__(self, memo_data: dict | None = None):
        """Initialize validator with optional memo data dictionary."""
        self.memo_data = memo_data or {}
        self.errors = []
        self.warnings = []

    def validate_all(self) -> ValidationResult:
        """Run all validations and return result."""
        self.errors = []
        self.warnings = []

        self.validate_required_fields()
        self.validate_date_format()
        self.validate_office_symbol()
        self.validate_rank_branch()
        self.validate_subject()
        self.validate_body_content()

        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
        )

    def validate_required_fields(self) -> None:
        """Check that all required fields are present."""
        required_fields = [
            ("ORGANIZATION_NAME", "Organization name"),
            ("ORGANIZATION_STREET_ADDRESS", "Organization street address"),
            ("ORGANIZATION_CITY_STATE_ZIP", "Organization city/state/ZIP"),
            ("OFFICE_SYMBOL", "Office symbol"),
            ("DATE", "Date"),
            ("SUBJECT", "Subject"),
            ("AUTHOR", "Author name"),
            ("RANK", "Rank"),
            ("BRANCH", "Branch"),
        ]

        for field_key, field_name in required_fields:
            value = self.memo_data.get(field_key, "").strip()
            if not value:
                self.errors.append(f"{field_name} is required")

    def validate_date_format(self) -> None:
        """Validate date is in correct Army format (DD Month YYYY)."""
        date_value = self.memo_data.get("DATE", "").strip()
        if not date_value:
            return  # Already caught by required fields

        if not self.DATE_PATTERN.match(date_value):
            self.errors.append(
                f"Date '{date_value}' should be in format 'DD Month YYYY' "
                "(e.g., '15 January 2025')"
            )
        else:
            # Check if date is reasonable (not too far in past/future)
            try:
                parsed_date = datetime.strptime(date_value, "%d %B %Y")
                today = datetime.now()
                days_diff = (parsed_date - today).days

                if days_diff > 365:
                    self.warnings.append(
                        f"Date '{date_value}' is more than a year in the future"
                    )
                elif days_diff < -365:
                    self.warnings.append(
                        f"Date '{date_value}' is more than a year in the past"
                    )
            except ValueError:
                pass  # Date pattern matched but parsing failed - rare edge case

    def validate_office_symbol(self) -> None:
        """Validate office symbol format."""
        office_symbol = self.memo_data.get("OFFICE_SYMBOL", "").strip()
        if not office_symbol:
            return  # Already caught by required fields

        if not self.OFFICE_SYMBOL_PATTERN.match(office_symbol):
            self.warnings.append(
                f"Office symbol '{office_symbol}' may not be in standard format "
                "(typically XXXX-XX-X, e.g., 'ATZB-CD-E')"
            )

    def validate_rank_branch(self) -> None:
        """Validate rank and branch are recognized."""
        rank = self.memo_data.get("RANK", "").strip().upper()
        branch = self.memo_data.get("BRANCH", "").strip().upper()

        if rank and rank not in self.VALID_RANKS:
            self.warnings.append(
                f"Rank '{rank}' is not a recognized Army rank abbreviation"
            )

        if branch and branch not in self.VALID_BRANCHES:
            self.warnings.append(
                f"Branch '{branch}' is not a recognized Army branch abbreviation"
            )

    def validate_subject(self) -> None:
        """Validate subject line."""
        subject = self.memo_data.get("SUBJECT", "").strip()
        if not subject:
            return  # Already caught by required fields

        if len(subject) > 150:
            self.warnings.append(
                f"Subject line is {len(subject)} characters. "
                "Consider keeping it under 150 characters for readability."
            )

        if not subject[0].isupper():
            self.warnings.append("Subject line should start with a capital letter")

    def validate_body_content(self) -> None:
        """Validate memo body content."""
        body = self.memo_data.get("BODY", "").strip()
        if not body:
            self.errors.append("Memo body content is required")
            return

        # Check for problematic LaTeX characters that might cause issues
        problematic_chars = ["$", "%", "&", "#", "_", "{", "}", "~", "^", "\\"]
        found_chars = [
            c for c in problematic_chars if c in body and f"\\{c}" not in body
        ]

        if found_chars:
            self.warnings.append(
                f"Body contains special LaTeX characters ({', '.join(found_chars)}) "
                "that may need escaping"
            )

        # Check minimum content length
        if len(body) < 50:
            self.warnings.append(
                "Memo body is quite short. Consider adding more detail."
            )

    @classmethod
    def validate_text_input(cls, text: str) -> ValidationResult:
        """Validate raw AMD format text input."""
        validator = cls()
        validator.errors = []
        validator.warnings = []

        if not text or not text.strip():
            validator.errors.append("Memo content is empty")
            return ValidationResult(is_valid=False, errors=validator.errors)

        # Parse basic structure
        lines = text.strip().split("\n")
        has_body = False

        for line in lines:
            line = line.strip()
            if line.startswith("---"):
                has_body = True
                break
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                validator.memo_data[key.strip()] = value.strip()

        if not has_body:
            validator.warnings.append(
                "Memo appears to be missing body content (no '---' separator found)"
            )

        # Run validations
        validator.validate_required_fields()
        validator.validate_date_format()
        validator.validate_office_symbol()
        validator.validate_rank_branch()
        validator.validate_subject()

        return ValidationResult(
            is_valid=len(validator.errors) == 0,
            errors=validator.errors,
            warnings=validator.warnings,
        )
