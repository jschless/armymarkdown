# ruff: noqa: SIM102, E741
"""
PDF validation service for AR 25-50 compliance checking.

Validates extracted PDF metadata against Army Regulation 25-50 formatting requirements.
"""

from dataclasses import dataclass, field
import re
from typing import ClassVar

from .memo_model import MemoParser, ParsedMemo
from .pdf_parser import PDFMetadata
from .rules import AR_25_50_RULES, Severity, get_rule_by_id


@dataclass
class ValidationIssue:
    """A single validation issue found in the PDF."""

    rule_id: str
    rule_name: str
    description: str
    severity: str
    ar_reference: str
    details: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "description": self.description,
            "severity": self.severity,
            "ar_reference": self.ar_reference,
            "details": self.details,
        }


@dataclass
class PDFValidationResult:
    """Complete validation result for a PDF document."""

    is_compliant: bool = False
    compliance_score: float = 0.0
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_compliant": self.is_compliant,
            "compliance_score": self.compliance_score,
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata_summary": self.metadata_summary,
        }


class PDFValidator:
    """Validate PDF documents against AR 25-50 requirements."""

    # Acceptable font name patterns (case-insensitive matching)
    ACCEPTABLE_FONT_PATTERNS: ClassVar[list[str]] = [
        r"arial",
        r"courier.*new",
        r"courier",
    ]

    # Date format pattern (DD Month YYYY)
    DATE_PATTERN = re.compile(
        r"\b\d{1,2}\s+(January|February|March|April|May|June|July|"
        r"August|September|October|November|December)\s+\d{4}\b",
        re.IGNORECASE,
    )

    def __init__(self, metadata: PDFMetadata):
        """
        Initialize validator with PDF metadata.

        Args:
            metadata: Extracted PDF metadata from PDFParser
        """
        self.metadata = metadata
        self.issues: list[ValidationIssue] = []
        self.rules_config = AR_25_50_RULES
        self.memo: ParsedMemo | None = None

    def validate_all(self) -> PDFValidationResult:
        """
        Run all validation checks and return results.

        Returns:
            PDFValidationResult with compliance status, score, and issues
        """
        self.issues = []

        # Parse the memo into structured format once
        parser = MemoParser(self.metadata)
        self.memo = parser.parse()

        # Check for extraction errors first
        if self.metadata.extraction_errors:
            for error in self.metadata.extraction_errors:
                self._add_issue(
                    rule_id="PARSE_001",
                    rule_name="PDF Parsing",
                    description="Error extracting PDF content",
                    severity=Severity.ERROR.value,
                    ar_reference="N/A",
                    details=error,
                )

        # Run all validation checks
        self.check_font_type()
        self.check_font_size()
        self.check_margins()
        self.check_department_line()
        self.check_date_format()
        self.check_subject_present()
        self.check_subject_format()
        self.check_memo_for_capitalization()
        self.check_signature_block()
        self.check_paragraph_numbering()
        self.check_subdivision_pairs()
        self.check_paragraph_indentation()
        self.check_max_subdivision_depth()
        self.check_line_continuation()
        self.check_vertical_spacing()
        self.check_sentence_spacing()
        self.check_signature_block_placement()
        self.check_continuation_page_header()
        self.check_paragraph_page_division()
        self.check_signature_with_last_paragraph()
        self.check_page_number_position()
        self.check_army_capitalization()
        self.check_acronym_usage()

        # Calculate compliance score
        error_count = len(
            [i for i in self.issues if i.severity == Severity.ERROR.value]
        )
        warning_count = len(
            [i for i in self.issues if i.severity == Severity.WARNING.value]
        )

        # Score calculation: errors have more weight than warnings
        deductions = error_count * 0.15 + warning_count * 0.05
        score = max(0.0, 1.0 - deductions)

        return PDFValidationResult(
            is_compliant=error_count == 0,
            compliance_score=round(score, 2),
            issues=self.issues,
            metadata_summary={
                "page_count": self.metadata.page_count,
                "fonts_detected": len(self.metadata.fonts),
                "text_length": len(self.metadata.text_content),
                "margins": self.metadata.margins,
            },
        )

    def _add_issue(
        self,
        rule_id: str,
        rule_name: str,
        description: str,
        severity: str,
        ar_reference: str,
        details: str = "",
    ) -> None:
        """Add a validation issue to the results."""
        self.issues.append(
            ValidationIssue(
                rule_id=rule_id,
                rule_name=rule_name,
                description=description,
                severity=severity,
                ar_reference=ar_reference,
                details=details,
            )
        )

    def _add_rule_issue(self, rule_id: str, details: str = "") -> None:
        """Add an issue based on a predefined rule ID."""
        rule = get_rule_by_id(rule_id)
        if rule:
            self._add_issue(
                rule_id=rule.id,
                rule_name=rule.name,
                description=rule.description,
                severity=rule.severity.value,
                ar_reference=rule.ar_reference,
                details=details,
            )

    def check_font_type(self) -> None:
        """Check if document uses acceptable fonts (Arial or Courier New)."""
        if not self.metadata.fonts:
            self._add_rule_issue(
                "FONT_001", "Unable to detect fonts in document (may be image-based)"
            )
            return

        acceptable_fonts = self.rules_config["font"]["acceptable"]

        # Find the dominant font (most characters)
        dominant_font = self.metadata.fonts[0] if self.metadata.fonts else None
        if not dominant_font:
            return

        font_name = dominant_font.get("name", "").lower()

        # Check if font matches any acceptable pattern
        is_acceptable = any(
            re.search(pattern, font_name) for pattern in self.ACCEPTABLE_FONT_PATTERNS
        )

        if not is_acceptable:
            self._add_rule_issue(
                "FONT_001",
                f"Document uses '{dominant_font.get('name')}' font. "
                f"Acceptable fonts: {', '.join(acceptable_fonts)}",
            )

    def check_font_size(self) -> None:
        """Check if document uses correct font size (12pt)."""
        if not self.metadata.fonts:
            return

        required_size = self.rules_config["font"]["size"]

        # Check the dominant font size
        dominant_font = self.metadata.fonts[0] if self.metadata.fonts else None
        if not dominant_font:
            return

        font_size = dominant_font.get("size", 0)

        # Allow some tolerance for font size (PDF rendering can have slight variations)
        size_tolerance = 1.0  # 1 point tolerance
        if abs(font_size - required_size) > size_tolerance:
            self._add_rule_issue(
                "FONT_002",
                f"Primary font size is {font_size}pt, should be {required_size}pt",
            )

    def check_margins(self) -> None:
        """Check if document margins meet requirements (1 inch all sides)."""
        margins = self.metadata.margins
        if not margins:
            self._add_rule_issue("MARGIN_001", "Unable to determine document margins")
            return

        tolerance = self.rules_config["margins"]["tolerance"]
        required = 1.0  # 1 inch

        margin_issues = []

        # Left margin should be approximately 1 inch (alignment matters)
        # Note: Top margin is not checked because LaTeX/PDF rendering varies
        # and the header positioning is handled by the template
        left_margin = margins.get("left", 0)
        if abs(left_margin - required) > tolerance:
            margin_issues.append(f'left: {left_margin}" (should be {required}")')

        # Right and bottom margins just need to be AT LEAST 1 inch
        # (text shouldn't extend too close to edge, but larger margin is fine
        # since memos are left-aligned with ragged right edge)
        for side in ["right", "bottom"]:
            actual = margins.get(side, 0)
            min_required = required - tolerance
            if actual < min_required:
                margin_issues.append(
                    f'{side}: {actual}" (should be at least {required}")'
                )

        if margin_issues:
            self._add_rule_issue("MARGIN_001", "; ".join(margin_issues))

    def check_department_line(self) -> None:
        """Check if 'DEPARTMENT OF THE ARMY' header is present."""
        if not self.memo.department_line:
            self._add_rule_issue(
                "HEADER_001",
                "Document should contain 'DEPARTMENT OF THE ARMY' header",
            )

    def check_date_format(self) -> None:
        """Check if date is in correct format (DD Month YYYY)."""
        if not self.memo.date:
            self._add_rule_issue(
                "DATE_001",
                "No date found in expected format (e.g., '15 January 2025')",
            )

    def check_subject_present(self) -> None:
        """Check if a subject line is present."""
        if not self.memo.subject_content:
            self._add_rule_issue(
                "SUBJECT_001",
                "No subject line detected (expected 'SUBJECT:' followed by memo topic)",
            )

    def check_subject_format(self) -> None:
        """
        Check SUBJECT line formatting.

        AR 25-50 requirements:
        - "SUBJECT:" must be in uppercase letters
        - Subject text should be 10 words or less
        """
        if not self.memo.subject_label:
            return

        issues = []

        # Check 1: "SUBJECT:" must be uppercase
        subject_word = re.match(r"([A-Za-z]+)", self.memo.subject_label)
        if subject_word and not subject_word.group(1).isupper():
            issues.append(
                f"'SUBJECT:' should be uppercase (found '{subject_word.group(1)}')"
            )

        # Check 2: Subject text should be 10 words or less
        if self.memo.subject_word_count > 10:
            issues.append(
                f"Subject has {self.memo.subject_word_count} words (should be 10 or less)"
            )

        if issues:
            self._add_issue(
                rule_id="SUBJECT_002",
                rule_name="Subject Line Format",
                description="SUBJECT: must be uppercase; subject text should be 10 words or less",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-3",
                details="; ".join(issues),
            )

    def check_memo_for_capitalization(self) -> None:
        """
        Check MEMORANDUM FOR line capitalization consistency.

        AR 25-50: "Type addresses in either all uppercase letters or uppercase
        and lowercase letters. Do not mix the two styles. Be consistent."
        """
        if not self.memo.memo_for_address:
            return

        if self.memo.memo_for_capitalization == "mixed":
            self._add_issue(
                rule_id="MEMO_FOR_001",
                rule_name="MEMORANDUM FOR Capitalization",
                description="Address must be consistently styled - all uppercase OR title case, not mixed",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-3(5)",
                details=f"Found mixed capitalization styles in '{self.memo.memo_for_address[:40]}...'",
            )

    def check_signature_block(self) -> None:
        """Check if a signature block is present."""
        if not self.memo.signature_block or (
            not self.memo.signature_block.name and not self.memo.signature_block.rank
        ):
            self._add_rule_issue(
                "SIG_001",
                "No signature block detected (expected name, rank, and title)",
            )

    def check_paragraph_numbering(self) -> None:
        """
        Check if paragraphs follow AR 25-50 numbering hierarchy.

        AR 25-50 specifies:
        - Level 1: 1., 2., 3. (at left margin)
        - Level 2: a., b., c. (indent 1/4 inch)
        - Level 3: (1), (2), (3) (indent 1/2 inch)
        - Level 4: (a), (b), (c) (indent 1/2 inch, same as level 3)
        - Do not subdivide beyond level 4
        """
        if not self.memo.paragraphs:
            self._add_issue(
                rule_id="BODY_001",
                rule_name="Paragraph Numbering",
                description="Body paragraphs should be numbered (1., 2., 3., etc.)",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-4",
                details="No numbered paragraphs found in document",
            )
            return

        # Check: must have at least one level 1 paragraph
        has_level1 = any(p.level == 1 for p in self.memo.paragraphs)
        if not has_level1:
            self._add_issue(
                rule_id="BODY_001",
                rule_name="Paragraph Numbering",
                description="Body paragraphs should be numbered (1., 2., 3., etc.)",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-4",
                details="No level 1 paragraphs (1., 2., 3.) found in document",
            )

    def check_subdivision_pairs(self) -> None:
        """
        Check that subdivided paragraphs have at least two sub-items.

        AR 25-50: "When a paragraph is subdivided, there must be at least two subparagraphs."
        If there's an "a." there must be a "b."
        """
        if not self.memo.paragraphs:
            return

        # Group paragraphs by their parent context
        # Track subdivisions within each parent
        level2_by_parent = {}  # level1_num -> set of level2 letters
        level3_by_parent = {}  # (level1_num, level2_letter) -> set of level3 numbers
        level4_by_parent = {}  # (level1_num, level2_letter, level3_num) -> set of level4 letters

        current_level1 = None
        current_level2 = None
        current_level3 = None

        for para in self.memo.paragraphs:
            if para.level == 1:
                current_level1 = para.number
                current_level2 = None
                current_level3 = None
            elif para.level == 2 and current_level1:
                current_level2 = para.number
                current_level3 = None
                if current_level1 not in level2_by_parent:
                    level2_by_parent[current_level1] = set()
                level2_by_parent[current_level1].add(para.number)
            elif para.level == 3 and current_level1 and current_level2:
                current_level3 = para.number
                key = (current_level1, current_level2)
                if key not in level3_by_parent:
                    level3_by_parent[key] = set()
                level3_by_parent[key].add(para.number)
            elif (
                para.level == 4 and current_level1 and current_level2 and current_level3
            ):
                key = (current_level1, current_level2, current_level3)
                if key not in level4_by_parent:
                    level4_by_parent[key] = set()
                level4_by_parent[key].add(para.number)

        # Check for lone sub-items
        issues = []

        for parent, subs in level2_by_parent.items():
            if len(subs) == 1:
                issues.append(
                    f"Paragraph {parent} has only sub-item '{next(iter(subs))}.' - need at least a. and b."
                )

        for parent, subs in level3_by_parent.items():
            if len(subs) == 1:
                issues.append(
                    f"Paragraph {parent[0]}.{parent[1]} has only sub-item ({next(iter(subs))}) - need at least (1) and (2)"
                )

        for parent, subs in level4_by_parent.items():
            if len(subs) == 1:
                issues.append(
                    f"Sub-paragraph ({parent[2]}) has only sub-item ({next(iter(subs))}) - need at least (a) and (b)"
                )

        if issues:
            self._add_issue(
                rule_id="BODY_002",
                rule_name="Subdivision Pairs",
                description="When subdividing, must have at least two sub-items (a AND b, not just a)",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-4",
                details="; ".join(issues[:3]),
            )

    def check_paragraph_indentation(self) -> None:
        """
        Check that paragraphs are indented correctly per AR 25-50.

        AR 25-50 specifies:
        - Level 1 (1., 2., 3.): at left margin (0 indent)
        - Level 2 (a., b., c.): indent 1/4 inch (18 points)
        - Level 3 ((1), (2), (3)): indent 1/2 inch (36 points)
        - Level 4 ((a), (b), (c)): indent 1/2 inch (36 points, same as level 3)
        """
        if not self.memo.paragraphs:
            return

        # Expected indents from left margin (in points)
        # Level 1: 0, Level 2: 18 (1/4"), Level 3/4: 36 (1/2")
        expected_indents = {
            1: 0,  # At left margin
            2: 18,  # 1/4 inch
            3: 36,  # 1/2 inch
            4: 36,  # 1/2 inch (same as level 3)
        }
        tolerance = 8  # ~0.11 inch tolerance

        issues = []

        # Find baseline x position from first level 1 paragraph
        baseline_x = None
        for para in self.memo.paragraphs:
            if para.level == 1:
                baseline_x = para.x_position
                break

        if baseline_x is None:
            return

        for para in self.memo.paragraphs:
            actual_indent = para.x_position - baseline_x
            expected_indent = expected_indents.get(para.level, 0)

            if abs(actual_indent - expected_indent) > tolerance:
                expected_inches = expected_indent / 72
                actual_inches = actual_indent / 72
                issues.append(
                    f"Level {para.level} '{para.number}. {para.content[:10]}...' indent: {actual_inches:.2f}\" (expected {expected_inches:.2f}\")"
                )

        if issues:
            self._add_issue(
                rule_id="BODY_004",
                rule_name="Paragraph Indentation",
                description='Paragraphs must be indented per AR 25-50 (1/4" for a/b/c, 1/2" for (1)/(2)/(a)/(b))',
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-4",
                details="; ".join(issues[:3]),
            )

    def check_max_subdivision_depth(self) -> None:
        """
        Check that paragraphs don't exceed maximum subdivision depth.

        AR 25-50: "Do not subdivide beyond the third subdivision."
        The hierarchy is:
        - Level 1: 1., 2., 3.
        - Level 2: a., b., c.
        - Level 3: (1), (2), (3)
        - Level 4: (a), (b), (c) - MAXIMUM
        - Level 5+: NOT ALLOWED
        """
        lines = self.metadata.lines
        if not lines:
            return

        # Get baseline from left margin
        left_margin_inches = self.metadata.margins.get("left", 1.0)
        left_margin_inches * 72

        # Maximum allowed indent is 1/2 inch (36 points) for levels 3-4
        max_allowed_indent = 36 + 15  # 36pt + tolerance

        # Patterns for valid paragraph markers (levels 1-4)
        # These must be followed by content (space or text)
        valid_marker_patterns = [
            re.compile(r"^\d+\.\s"),  # Level 1: "1. " or "1.TEXT"
            re.compile(r"^[a-z]\.\s"),  # Level 2: "a. "
            re.compile(r"^\(\d+\)\s"),  # Level 3: "(1) "
            re.compile(r"^\([a-z]\)\s"),  # Level 4: "(a) "
        ]

        # Patterns that indicate invalid level 5+ attempts
        # These are specific numbering formats that shouldn't appear
        invalid_patterns = [
            re.compile(r"^\[\d+\]\s"),  # [1], [2], [3]
            re.compile(r"^\[[a-z]\]\s"),  # [a], [b], [c]
            re.compile(r"^\(\([a-z]\)\)"),  # ((a)), ((b))
            re.compile(r"^\(\(\d+\)\)"),  # ((1)), ((2))
            re.compile(r"^[ivx]+\.\s", re.I),  # Roman numerals: i., ii., iii.
            re.compile(r"^\([ivx]+\)\s", re.I),  # (i), (ii), (iii)
        ]

        # Pattern to identify actual list markers (not just any text)
        list_marker_pattern = re.compile(
            r"^(\d+\.|[a-z]\.|[A-Z]\.|\(\d+\)|\([a-z]\)|\([A-Z]\)|\[\d+\]|\[[a-z]\])\s"
        )

        issues = []
        baseline_x = None

        for line in lines:
            text = line.get("text", "").strip()
            x_start = line.get("x_start", 0)

            if not text or len(text) < 3:
                continue

            # Set baseline from first level 1 paragraph
            if re.match(r"^\d+\.\s*\S", text) and baseline_x is None:
                baseline_x = x_start

            if baseline_x is None:
                continue

            # Check for invalid level 5+ numbering patterns
            for pattern in invalid_patterns:
                if pattern.match(text):
                    issues.append(f"Invalid subdivision format: '{text[:25]}...'")
                    break

            # Check for excessive indentation only on actual list items
            actual_indent = x_start - baseline_x

            # Only flag if this looks like a list marker AND is excessively indented
            if list_marker_pattern.match(text) and actual_indent > max_allowed_indent:
                # Verify it's not a valid level 1-4 marker at correct position
                is_valid = any(p.match(text) for p in valid_marker_patterns)
                if not is_valid or actual_indent > max_allowed_indent + 20:
                    issues.append(
                        f"Excessive indentation ({actual_indent / 72:.2f}\") for '{text[:25]}...' - max is 1/2\""
                    )

        if issues:
            self._add_issue(
                rule_id="BODY_005",
                rule_name="Maximum Subdivision Depth",
                description="Do not subdivide beyond level 4 ((a), (b), (c)) or indent beyond 1/2 inch",
                severity=Severity.ERROR.value,
                ar_reference="AR 25-50, para 2-4",
                details="; ".join(issues[:3]),
            )

    def check_line_continuation(self) -> None:
        """
        Check that continuation lines return to the left margin.

        In AR 25-50 format, when a numbered paragraph wraps to the next line,
        the continuation should start at the left margin, NOT indented under
        the first word (no hanging indent).
        """
        lines = self.metadata.lines
        if not lines:
            return

        # Determine the left margin from the document
        left_margin_inches = self.metadata.margins.get("left", 1.0)
        left_margin_points = left_margin_inches * 72

        # Only consider lines in the body text area (within ~3 inches of left margin)
        # This filters out page numbers, headers, etc. on the right side
        max_body_x = left_margin_points + 216  # ~3 inches from left margin

        # Patterns to identify paragraph starts
        para_start_pattern = re.compile(r"^(\d+\.|[a-z]\.|[A-Z]\.|\(\d+\)|\([a-z]\))")

        hanging_indent_issues = []
        prev_line = None

        for line in lines:
            text = line.get("text", "").strip()
            x_start = line.get("x_start", 0)

            # Skip empty lines
            if not text:
                prev_line = None
                continue

            # Skip lines that are clearly not body text (page numbers, etc.)
            if x_start > max_body_x:
                continue

            # Skip very short lines (likely page numbers or artifacts)
            if len(text) < 5:
                continue

            # If this is NOT a new paragraph start, check if it's a continuation
            if prev_line and not para_start_pattern.match(text):
                prev_text = prev_line.get("text", "").strip()
                prev_x = prev_line.get("x_start", 0)

                # If previous line started a numbered paragraph
                if para_start_pattern.match(prev_text):
                    # This continuation line should be at left margin, not indented
                    # Check if it's significantly indented (hanging indent style)
                    # A hanging indent would place text under the first word, not the number

                    # If continuation is indented more than the paragraph start + tolerance
                    # it's likely a hanging indent
                    if x_start > prev_x + 15:  # More than ~0.2 inches past the number
                        hanging_indent_issues.append(
                            f"Line '{text[:30]}...' appears to use hanging indent"
                        )

            prev_line = line

        if hanging_indent_issues:
            self._add_issue(
                rule_id="BODY_003",
                rule_name="Line Continuation",
                description="Continuation lines should return to left margin (no hanging indent)",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-4",
                details="; ".join(hanging_indent_issues[:3]),  # Limit to first 3
            )

    def check_vertical_spacing(self) -> None:
        """
        Check vertical spacing between document elements.

        AR 25-50 spacing requirements:
        - 2 blank lines between office symbol/date and MEMORANDUM FOR
        - 2 blank lines between SUBJECT and first paragraph
        - 4 blank lines between last paragraph and signature block
        - 1 blank line between paragraphs
        """
        lines = self.metadata.lines
        if not lines:
            return

        # Approximate line height in points (12pt font = ~14pt line height)

        # Expected gaps (in points, approximate)
        # 1 blank line = ~14pt, 2 blank lines = ~28pt, 4 blank lines = ~56pt
        two_lines_min = 35  # At least ~2.5 line heights for 2 blank lines
        four_lines_min = 70  # At least ~5 line heights for 4 blank lines

        issues = []

        # Find key elements and their positions
        memo_for_line = None
        subject_line = None
        first_para_line = None
        signature_line = None
        office_symbol_line = None

        # Patterns
        memo_for_pattern = re.compile(r"MEMORANDUM\s*FOR", re.IGNORECASE)
        subject_pattern = re.compile(r"SUBJECT\s*:", re.IGNORECASE)
        first_para_pattern = re.compile(r"^1\.")
        office_symbol_pattern = re.compile(r"^[A-Z]{2,}-[A-Z0-9-]+")

        # Track all numbered paragraphs to find the last one
        last_numbered_para = None

        for _i, line in enumerate(lines):
            text = line.get("text", "").strip()
            _ = line.get("page", 0)

            if not text:
                continue

            # Find office symbol (usually contains date on same line or nearby)
            if office_symbol_pattern.match(text) and office_symbol_line is None:
                office_symbol_line = line

            # Find MEMORANDUM FOR
            if memo_for_pattern.search(text) and memo_for_line is None:
                memo_for_line = line

            # Find SUBJECT line (first occurrence only, not headers on subsequent pages)
            if subject_pattern.match(text) and subject_line is None:
                subject_line = line

            # Find first paragraph (1.)
            if first_para_pattern.match(text) and first_para_line is None:
                first_para_line = line

            # Track numbered paragraphs to find the last one
            if re.match(r"^\d+\.", text):
                last_numbered_para = line

        # Find signature block (look for all caps name pattern after last paragraph)
        if last_numbered_para:
            last_para_idx = lines.index(last_numbered_para)
            for line in lines[last_para_idx:]:
                text = line.get("text", "").strip()
                # Signature block typically has all caps name
                if re.match(r"^[A-Z\s\.]+$", text) and len(text) > 5:
                    # Check it's not just a header
                    if "DEPARTMENT" not in text and "MEMORANDUM" not in text:
                        signature_line = line
                        break

        # Check spacing: Office symbol to MEMORANDUM FOR (2 blank lines)
        if office_symbol_line and memo_for_line:
            if office_symbol_line.get("page") == memo_for_line.get("page"):
                gap = memo_for_line.get("y_pos", 0) - office_symbol_line.get("y_pos", 0)
                if gap < two_lines_min:
                    issues.append(
                        f"Office symbol to MEMORANDUM FOR: {gap:.0f}pt gap (need ~{two_lines_min}pt for 2 blank lines)"
                    )

        # Check spacing: SUBJECT to first paragraph (2 blank lines)
        if subject_line and first_para_line:
            if subject_line.get("page") == first_para_line.get("page"):
                gap = first_para_line.get("y_pos", 0) - subject_line.get("y_pos", 0)
                if gap < two_lines_min:
                    issues.append(
                        f"SUBJECT to first paragraph: {gap:.0f}pt gap (need ~{two_lines_min}pt for 2 blank lines)"
                    )

        # Check spacing: Last paragraph to signature block (4 blank lines)
        if last_numbered_para and signature_line:
            if last_numbered_para.get("page") == signature_line.get("page"):
                # Need to find the actual last line of the last paragraph, not just the start
                last_para_idx = lines.index(last_numbered_para)
                sig_idx = lines.index(signature_line)

                # Find the last content line before signature
                last_content_line = last_numbered_para
                for line in lines[last_para_idx:sig_idx]:
                    text = line.get("text", "").strip()
                    if text and line.get("page") == signature_line.get("page"):
                        # Skip if it looks like part of signature block
                        if not re.match(r"^[A-Z\s\.]+$", text):
                            last_content_line = line

                gap = signature_line.get("y_pos", 0) - last_content_line.get("y_pos", 0)
                if gap < four_lines_min:
                    issues.append(
                        f"Last paragraph to signature: {gap:.0f}pt gap (need ~{four_lines_min}pt for 4 blank lines)"
                    )

        if issues:
            self._add_issue(
                rule_id="SPACING_001",
                rule_name="Vertical Spacing",
                description="Document sections must have correct vertical spacing",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-2",
                details="; ".join(issues[:3]),
            )

    def check_sentence_spacing(self) -> None:
        """
        Check spacing after punctuation.

        AR 25-50 traditionally requires:
        - Two spaces after ending punctuation (periods, question marks)
        - One space after other punctuation

        Note: This check is informational only since:
        1. PDF text extraction doesn't reliably preserve spacing
        2. Modern typesetting standards often use single space
        3. LaTeX automatically handles spacing
        """
        # Skip this check for now as PDF extraction doesn't reliably
        # preserve character-level spacing information.
        # The LaTeX template handles this automatically.
        pass

    def check_signature_block_placement(self) -> None:
        """
        Check that signature block is not alone on its own page.

        The signature block must have at least one body paragraph on the same page.
        """
        if not self.memo.signature_block:
            return

        signature_page = self.memo.signature_block.page

        # Check if there's any paragraph on the same page as the signature
        has_body_content = any(
            para.page == signature_page for para in self.memo.paragraphs
        )

        if not has_body_content:
            self._add_issue(
                rule_id="SPACING_003",
                rule_name="Signature Block Placement",
                description="Signature block must not be alone on a page - must have body content",
                severity=Severity.ERROR.value,
                ar_reference="AR 25-50, para 2-5",
                details=f"Signature block is alone on page {signature_page + 1}",
            )

    def check_continuation_page_header(self) -> None:
        """
        Check continuation page headers.

        AR 25-50 requirements for multi-page memos:
        - Office symbol at left margin, 1 inch from top
        - Subject on the line below the office symbol
        """
        if self.memo.page_count < 2:
            return  # Only applies to multi-page documents

        # Expected positions
        one_inch_pts = 72
        tolerance = 10  # ~0.14 inch tolerance

        issues = []

        # Check each continuation page (pages 2+)
        for page_num in range(1, self.memo.page_count):
            # Find header for this page
            header = next(
                (h for h in self.memo.continuation_headers if h.page == page_num), None
            )

            if not header:
                issues.append(f"Page {page_num + 1}: Missing continuation header")
                continue

            # Check office symbol position (should be ~1 inch from top)
            if abs(header.office_symbol_y - one_inch_pts) > tolerance:
                issues.append(
                    f'Page {page_num + 1}: Office symbol at {header.office_symbol_y / 72:.2f}" from top (should be 1")'
                )

            # Check subject is present and on line below office symbol
            if header.subject:
                gap = header.subject_y - header.office_symbol_y
                # Should be roughly one line height (~14-20pt)
                if gap < 10 or gap > 30:
                    issues.append(
                        f"Page {page_num + 1}: Subject should be on line below office symbol"
                    )
            else:
                issues.append(f"Page {page_num + 1}: Missing subject line in header")

        if issues:
            self._add_issue(
                rule_id="PAGE_001",
                rule_name="Continuation Page Header",
                description='Continuation pages must have office symbol (1" from top) and subject',
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-3",
                details="; ".join(issues[:3]),
            )

    def check_paragraph_page_division(self) -> None:
        """
        Check paragraph division between pages.

        AR 25-50 requirements:
        - Do not divide a paragraph of 3 lines or fewer between pages
        - At least 2 lines of divided paragraph must appear on each page
        """
        if self.metadata.page_count < 2:
            return

        lines = self.metadata.lines
        if not lines:
            return

        issues = []

        # Group lines by page
        pages = {}
        for line in lines:
            page = line.get("page", 0)
            if page not in pages:
                pages[page] = []
            pages[page].append(line)

        # Check each page boundary
        for page_num in range(self.metadata.page_count - 1):
            if page_num not in pages or (page_num + 1) not in pages:
                continue

            current_page = pages[page_num]
            next_page = pages[page_num + 1]

            # Get last few lines of current page (excluding page numbers)
            last_lines = [
                l for l in current_page if len(l.get("text", "").strip()) > 3
            ][-5:]

            # Get first content lines of next page (skip header)
            first_lines = []
            for line in next_page:
                text = line.get("text", "").strip()
                # Skip header elements
                if re.match(r"^[A-Z]{2,}-[A-Z0-9-]*$", text):  # Office symbol
                    continue
                if re.match(r"^SUBJECT\s*:", text, re.IGNORECASE):
                    continue
                if len(text) > 3:
                    first_lines.append(line)
                if len(first_lines) >= 5:
                    break

            # Check if a paragraph is split across pages
            # Look for continuation (line that doesn't start with paragraph marker)
            if first_lines:
                first_content = first_lines[0].get("text", "").strip()
                # If first content doesn't start a new paragraph, it's a continuation
                if not re.match(
                    r"^(\d+\.|[a-z]\.|[A-Z]\.|\(\d+\)|\([a-z]\))", first_content
                ):
                    # Count how many non-paragraph-start lines at end of current page
                    trailing_continuation = 0
                    for line in reversed(last_lines):
                        text = line.get("text", "").strip()
                        if re.match(
                            r"^(\d+\.|[a-z]\.|[A-Z]\.|\(\d+\)|\([a-z]\))", text
                        ):
                            break
                        trailing_continuation += 1

                    # Count continuation lines at start of next page
                    leading_continuation = 0
                    for line in first_lines:
                        text = line.get("text", "").strip()
                        if re.match(
                            r"^(\d+\.|[a-z]\.|[A-Z]\.|\(\d+\)|\([a-z]\))", text
                        ):
                            break
                        leading_continuation += 1

                    # Check: at least 2 lines on each page for divided paragraphs
                    if trailing_continuation == 1:
                        issues.append(
                            f"Page {page_num + 1}: Only 1 line before page break (need at least 2)"
                        )
                    if leading_continuation == 1 and leading_continuation < len(
                        first_lines
                    ):
                        issues.append(
                            f"Page {page_num + 2}: Only 1 continuation line after page break (need at least 2)"
                        )

        if issues:
            self._add_issue(
                rule_id="PAGE_002",
                rule_name="Paragraph Page Division",
                description="Divided paragraphs must have at least 2 lines on each page",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-3",
                details="; ".join(issues[:3]),
            )

    def check_signature_with_last_paragraph(self) -> None:
        """
        Check signature block placement with last paragraph.

        AR 25-50: Do not type authority line and signature block on continuation
        page without at least 2 lines of the last paragraph. Exception: if last
        paragraph has only 1 line, it may be placed alone with signature.
        """
        if self.memo.page_count < 2:
            return

        if not self.memo.signature_block:
            return

        signature_page = self.memo.signature_block.page

        if signature_page == 0:
            return  # Signature on first page

        # Find paragraphs on the same page as signature
        paras_on_sig_page = [
            p for p in self.memo.paragraphs if p.page == signature_page
        ]

        # Check: need at least one paragraph (with 2+ lines) on signature page
        # Unless the entire last paragraph is only 1 line
        if not paras_on_sig_page:
            self._add_issue(
                rule_id="PAGE_003",
                rule_name="Signature Block Content",
                description="Signature block page must have body content (at least 2 lines of last paragraph)",
                severity=Severity.ERROR.value,
                ar_reference="AR 25-50, para 2-3",
                details=f"No body content on page {signature_page + 1} with signature block",
            )
            return

        # Check if the last paragraph on signature page has at least 2 lines
        last_para = paras_on_sig_page[-1]
        if last_para.line_count < 2:
            # This is acceptable if the entire paragraph is only 1 line
            # but we should check the total paragraph not just the portion on this page
            pass  # Allow single-line last paragraphs

    def check_page_number_position(self) -> None:
        """
        Check page number positioning.

        AR 25-50: Center page number approximately 1 inch from bottom of page.
        """
        if self.memo.page_count < 2:
            return  # Page numbers typically only on multi-page docs

        # Page dimensions
        page_height = 792  # 11 inches in points
        one_inch_from_bottom = page_height - 72  # ~720 points from top
        tolerance = 15  # ~0.2 inch tolerance
        page_center = 306  # Center of 8.5" page in points

        issues = []

        # Check each continuation page for page number
        for page_num in range(1, self.memo.page_count):  # Skip first page
            page_number_info = self.memo.page_numbers.get(page_num)

            if not page_number_info:
                continue  # Page number not found on this page

            y_pos = page_number_info.get("y", 0)
            x_pos = page_number_info.get("x", 0)

            # Check vertical position (1 inch from bottom)
            if abs(y_pos - one_inch_from_bottom) > tolerance:
                dist_from_bottom = (page_height - y_pos) / 72
                issues.append(
                    f'Page {page_num + 1}: Page number {dist_from_bottom:.2f}" from bottom (should be ~1")'
                )

            # Check horizontal centering
            if abs(x_pos - page_center) > 50:  # Allow some tolerance for centering
                issues.append(f"Page {page_num + 1}: Page number may not be centered")

        if issues:
            self._add_issue(
                rule_id="PAGE_004",
                rule_name="Page Number Position",
                description="Page numbers should be centered, 1 inch from bottom",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, para 2-3",
                details="; ".join(issues[:3]),
            )

    def check_army_capitalization(self) -> None:
        """
        Check capitalization of Army-specific terms.

        AR 25-50 style preferences:
        - Capitalize "Soldier" when referring to U.S. Army Soldier
        - Capitalize "Family" when referring to U.S. Army Family
        - Capitalize "Civilian" when referring to Army Civilians
          (especially when used with Soldier and/or Family)
        """
        text = self.memo.full_text
        if not text:
            return

        issues = []

        # Check for lowercase "soldier" that should be capitalized
        # Look for standalone word "soldier" or "soldiers" (not part of another word)
        lowercase_soldier = re.findall(r"\b(soldier|soldiers)\b", text, re.IGNORECASE)
        incorrect_soldier = [s for s in lowercase_soldier if s[0].islower()]
        if incorrect_soldier:
            issues.append(
                f"Found {len(incorrect_soldier)} instance(s) of lowercase 'soldier' (should be 'Soldier')"
            )

        # Check for lowercase "family" in Army context
        # Look for patterns like "Army family", "military family", "soldier's family"
        family_patterns = [
            r"\b(army|military|soldier'?s?)\s+(family|families)\b",
            r"\b(family|families)\s+(member|members|readiness|support)\b",
        ]
        for pattern in family_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Check if "family" part is lowercase
                full_match = " ".join(match)
                if "family" in full_match.lower() and "Family" not in full_match:
                    issues.append(
                        "Found lowercase 'family' in Army context (should be 'Family')"
                    )
                    break

        # Check for lowercase "civilian" when used with Soldier/Family
        civilian_context = re.findall(
            r"\b(soldier|family)\b.{0,30}\b(civilian|civilians)\b", text, re.IGNORECASE
        )
        for match in civilian_context:
            if match[1][0].islower():
                issues.append(
                    "Found lowercase 'civilian' used with Soldier/Family (should be 'Civilian')"
                )
                break

        if issues:
            self._add_issue(
                rule_id="STYLE_001",
                rule_name="Army Term Capitalization",
                description="Capitalize Soldier, Family, and Civilian when referring to Army personnel",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, Appendix A",
                details="; ".join(issues[:3]),
            )

    def check_acronym_usage(self) -> None:
        """
        Check acronym usage in the document.

        AR 25-50 guidelines:
        - Spell out acronym first time, then use acronym in parentheses
        - Don't overuse acronyms
        - Avoid using acronyms in subject line
        """
        text = self.memo.full_text
        if not text:
            return

        issues = []

        # Common military acronyms to check
        common_acronyms = [
            "POC",
            "NLT",
            "IAW",
            "TDY",
            "PCS",
            "AWOL",
            "NCO",
            "NCOIC",
            "OIC",
            "XO",
            "CO",
            "CSM",
            "1SG",
            "SOP",
            "OPORD",
            "FRAGO",
            "AAR",
            "COA",
            "IPR",
            "USR",
            "METL",
            "MOS",
            "ASI",
            "SQI",
        ]

        # Check for acronyms in subject line
        if self.memo.subject_content:
            for acronym in common_acronyms:
                if re.search(rf"\b{acronym}\b", self.memo.subject_content):
                    issues.append(
                        f"Acronym '{acronym}' found in subject line (avoid acronyms in subject)"
                    )
                    break  # Only report first one

        # Find all uppercase acronym-like words (2-6 capital letters)
        potential_acronyms = re.findall(r"\b([A-Z]{2,6})\b", text)

        # Filter to actual acronyms (appear multiple times or are known)
        acronym_counts = {}
        for acr in potential_acronyms:
            if acr not in acronym_counts:
                acronym_counts[acr] = 0
            acronym_counts[acr] += 1

        # Check for overuse of acronyms (more than 10 different acronyms)
        unique_acronyms = [a for a in acronym_counts if a in common_acronyms]
        if len(unique_acronyms) > 10:
            issues.append(
                f"Document uses {len(unique_acronyms)} different military acronyms (avoid overuse)"
            )

        if issues:
            self._add_issue(
                rule_id="STYLE_002",
                rule_name="Acronym Usage",
                description="Spell out acronyms on first use; avoid acronyms in subject line",
                severity=Severity.WARNING.value,
                ar_reference="AR 25-50, Appendix A",
                details="; ".join(issues[:3]),
            )
