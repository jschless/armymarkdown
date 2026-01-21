"""
Structured memo model for AR 25-50 validation.

Parses PDF metadata into a structured representation of an Army memorandum,
enabling cleaner validation logic.
"""

from dataclasses import dataclass, field
import re
from typing import ClassVar

from .pdf_parser import PDFMetadata


@dataclass
class Paragraph:
    """A single paragraph or sub-paragraph in the memo body."""

    number: str  # e.g., "1", "a", "(1)", "(a)"
    level: int  # 1=main, 2=a/b/c, 3=(1)/(2), 4=(a)/(b)
    content: str
    line_count: int
    page: int
    x_position: float  # indentation in points
    y_position: float


@dataclass
class SignatureBlock:
    """The signature block at the end of the memo."""

    name: str = ""
    rank: str = ""
    branch: str = ""
    title: str = ""
    page: int = 0
    y_position: float = 0


@dataclass
class ContinuationHeader:
    """Header on continuation pages."""

    office_symbol: str
    subject: str
    page: int
    office_symbol_y: float
    subject_y: float


@dataclass
class ParsedMemo:
    """Structured representation of an Army memorandum."""

    # Header elements (first page)
    department_line: str = ""
    organization_name: str = ""
    organization_address: list[str] = field(default_factory=list)
    office_symbol: str = ""
    date: str = ""

    # MEMORANDUM FOR line
    memorandum_for: str = ""
    memo_for_address: str = ""
    memo_for_capitalization: str = ""  # "upper", "title", or "mixed"

    # Subject line
    subject_label: str = ""  # "SUBJECT:" as it appears
    subject_content: str = ""
    subject_word_count: int = 0

    # Body paragraphs
    paragraphs: list[Paragraph] = field(default_factory=list)

    # Signature block
    signature_block: SignatureBlock | None = None

    # Multi-page info
    page_count: int = 1
    continuation_headers: list[ContinuationHeader] = field(default_factory=list)
    page_numbers: dict[int, dict] = field(default_factory=dict)  # page -> {y, x, value}

    # Text content for style checks
    full_text: str = ""

    # Raw line data for fallback checks
    lines: list[dict] = field(default_factory=list)


class MemoParser:
    """Parse PDF metadata into a structured ParsedMemo."""

    # Patterns for identifying memo elements
    DEPT_PATTERN = re.compile(r"DEPARTMENT\s*OF\s*THE\s*ARMY", re.IGNORECASE)
    OFFICE_SYMBOL_PATTERN = re.compile(r"^([A-Z]{2,}-[A-Z0-9-]+)")
    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)\s+\d{4})\b",
        re.IGNORECASE,
    )
    MEMO_FOR_PATTERN = re.compile(r"MEMORANDUM\s*FOR\s*(.+)", re.IGNORECASE)
    SUBJECT_PATTERN = re.compile(r"^(SUBJECT\s*:)\s*(.+)", re.IGNORECASE)

    # Paragraph level patterns
    LEVEL1_PATTERN = re.compile(r"^(\d+)\.\s*(.+)")  # 1., 2., 3.
    LEVEL2_PATTERN = re.compile(r"^([a-z])\.\s*(.+)")  # a., b., c.
    LEVEL3_PATTERN = re.compile(r"^\((\d+)\)\s*(.+)")  # (1), (2), (3)
    LEVEL4_PATTERN = re.compile(r"^\(([a-z])\)\s*(.+)")  # (a), (b), (c)

    # Rank patterns for signature block
    RANK_PATTERNS: ClassVar[list[str]] = [
        r"\b(PVT|PV2|PFC|SPC|CPL|SGT|SSG|SFC|MSG|1SG|SGM|CSM|SMA)\b",
        r"\b(WO1|CW2|CW3|CW4|CW5)\b",
        r"\b(2LT|1LT|CPT|MAJ|LTC|COL|BG|MG|LTG|GEN)\b",
    ]

    def __init__(self, metadata: PDFMetadata):
        """Initialize parser with PDF metadata."""
        self.metadata = metadata
        self.lines = metadata.lines
        self.text = metadata.text_content

    def parse(self) -> ParsedMemo:
        """Parse PDF metadata into a structured memo."""
        memo = ParsedMemo()
        memo.page_count = self.metadata.page_count
        memo.full_text = self.text
        memo.lines = self.lines

        # Parse each component
        self._parse_header(memo)
        self._parse_memo_for(memo)
        self._parse_subject(memo)
        self._parse_body_paragraphs(memo)
        self._parse_signature_block(memo)
        self._parse_continuation_headers(memo)
        self._parse_page_numbers(memo)

        return memo

    def _parse_header(self, memo: ParsedMemo) -> None:
        """Parse the header section (DEPARTMENT OF THE ARMY, org info, etc.)."""
        # Find DEPARTMENT OF THE ARMY
        if self.DEPT_PATTERN.search(self.text):
            memo.department_line = "DEPARTMENT OF THE ARMY"

        # Find office symbol and date (usually on same line or nearby)
        for line in self.lines:
            text = line.get("text", "").strip()
            page = line.get("page", 0)

            if page > 0:
                break  # Only look at first page for main header

            match = self.OFFICE_SYMBOL_PATTERN.match(text)
            if match:
                memo.office_symbol = match.group(1)
                # Check for date on same line
                date_match = self.DATE_PATTERN.search(text)
                if date_match:
                    memo.date = date_match.group(1)

            # Check for standalone date
            if not memo.date:
                date_match = self.DATE_PATTERN.search(text)
                if date_match:
                    memo.date = date_match.group(1)

        # Fallback: search text_content directly if lines is empty or date not found
        if not memo.date and self.text:
            date_match = self.DATE_PATTERN.search(self.text)
            if date_match:
                memo.date = date_match.group(1)

    def _parse_memo_for(self, memo: ParsedMemo) -> None:
        """Parse the MEMORANDUM FOR line."""
        found = False
        for line in self.lines:
            text = line.get("text", "").strip()

            match = self.MEMO_FOR_PATTERN.match(text)
            if match:
                memo.memorandum_for = text
                memo.memo_for_address = match.group(1)
                found = True
                break

        # Fallback: search text_content directly if lines is empty
        if not found and self.text:
            for line in self.text.split("\n"):
                match = self.MEMO_FOR_PATTERN.match(line.strip())
                if match:
                    memo.memorandum_for = line.strip()
                    memo.memo_for_address = match.group(1)
                    break

        # Analyze capitalization if we found a MEMORANDUM FOR line
        if memo.memo_for_address:
            address = memo.memo_for_address
            words = re.findall(r"[A-Za-z]+", address)

            if len(words) > 1:
                all_upper = sum(1 for w in words if w.isupper() and len(w) > 1)
                title_case = sum(
                    1
                    for w in words
                    if w[0].isupper() and not w.isupper() and len(w) > 1
                )

                if all_upper > 0 and title_case > 0:
                    memo.memo_for_capitalization = "mixed"
                elif all_upper > title_case:
                    memo.memo_for_capitalization = "upper"
                else:
                    memo.memo_for_capitalization = "title"

    def _parse_subject(self, memo: ParsedMemo) -> None:
        """Parse the SUBJECT line."""
        for line in self.lines:
            text = line.get("text", "").strip()
            page = line.get("page", 0)

            # Only check first page for main subject
            if page > 0:
                break

            match = self.SUBJECT_PATTERN.match(text)
            if match:
                memo.subject_label = match.group(1)
                memo.subject_content = match.group(2)
                # Count words
                words = memo.subject_content.split()
                memo.subject_word_count = len(words)
                break

        # Fallback: search text_content directly if lines is empty or subject not found
        if not memo.subject_content and self.text:
            # Search line by line in text_content
            for line in self.text.split("\n"):
                match = self.SUBJECT_PATTERN.match(line.strip())
                if match:
                    memo.subject_label = match.group(1)
                    memo.subject_content = match.group(2)
                    words = memo.subject_content.split()
                    memo.subject_word_count = len(words)
                    break

    def _parse_body_paragraphs(self, memo: ParsedMemo) -> None:
        """Parse body paragraphs with their structure."""
        current_para_lines = []
        current_para_start = None

        for line in self.lines:
            text = line.get("text", "").strip()
            page = line.get("page", 0)
            x = line.get("x_start", 0)
            y = line.get("y_pos", 0)

            if not text or len(text) < 3:
                continue

            # Skip header elements
            if self.OFFICE_SYMBOL_PATTERN.match(text) and len(text) < 20:
                continue
            if self.SUBJECT_PATTERN.match(text):
                continue
            if self.MEMO_FOR_PATTERN.match(text):
                continue
            if self.DEPT_PATTERN.search(text):
                continue

            # Check for paragraph start
            level = None
            number = None
            content = None

            match = self.LEVEL1_PATTERN.match(text)
            if match:
                level, number, content = 1, match.group(1), match.group(2)

            if not level:
                match = self.LEVEL2_PATTERN.match(text)
                if match:
                    level, number, content = 2, match.group(1), match.group(2)

            if not level:
                match = self.LEVEL3_PATTERN.match(text)
                if match:
                    level, number, content = 3, match.group(1), match.group(2)

            if not level:
                match = self.LEVEL4_PATTERN.match(text)
                if match:
                    level, number, content = 4, match.group(1), match.group(2)

            if level:
                # Save previous paragraph if exists
                if current_para_start is not None:
                    para = Paragraph(
                        number=current_para_start["number"],
                        level=current_para_start["level"],
                        content=current_para_start["content"],
                        line_count=len(current_para_lines),
                        page=current_para_start["page"],
                        x_position=current_para_start["x"],
                        y_position=current_para_start["y"],
                    )
                    memo.paragraphs.append(para)

                # Start new paragraph
                current_para_start = {
                    "number": number,
                    "level": level,
                    "content": content,
                    "page": page,
                    "x": x,
                    "y": y,
                }
                current_para_lines = [line]
            elif current_para_start is not None:
                # Continuation line
                current_para_lines.append(line)

        # Don't forget last paragraph
        if current_para_start is not None:
            para = Paragraph(
                number=current_para_start["number"],
                level=current_para_start["level"],
                content=current_para_start["content"],
                line_count=len(current_para_lines),
                page=current_para_start["page"],
                x_position=current_para_start["x"],
                y_position=current_para_start["y"],
            )
            memo.paragraphs.append(para)

    def _parse_signature_block(self, memo: ParsedMemo) -> None:
        """Parse the signature block."""
        sig_block = SignatureBlock()

        for line in self.lines:
            text = line.get("text", "").strip()
            page = line.get("page", 0)
            x = line.get("x_start", 0)
            y = line.get("y_pos", 0)

            # Signature block is usually right-aligned (x > 200)
            if x < 200:
                continue

            # Check for rank
            for pattern in self.RANK_PATTERNS:
                if re.search(pattern, text):
                    sig_block.rank = text
                    sig_block.page = page
                    sig_block.y_position = y
                    break

            # Check for all-caps name (before rank line)
            if (
                not sig_block.name
                and re.match(r"^[A-Z\s\.]+$", text)
                and len(text) > 5
                and "DEPARTMENT" not in text
                and "MEMORANDUM" not in text
            ):
                sig_block.name = text
                sig_block.page = page
                sig_block.y_position = y

        if sig_block.name or sig_block.rank:
            memo.signature_block = sig_block

    def _parse_continuation_headers(self, memo: ParsedMemo) -> None:
        """Parse headers on continuation pages."""
        if memo.page_count < 2:
            return

        for page_num in range(1, memo.page_count):
            page_lines = [line for line in self.lines if line.get("page") == page_num]

            office_symbol = None
            office_symbol_y = 0
            subject = None
            subject_y = 0

            for line in page_lines[:10]:  # Check first 10 lines
                text = line.get("text", "").strip()
                y = line.get("y_pos", 0)

                if self.OFFICE_SYMBOL_PATTERN.match(text) and not office_symbol:
                    office_symbol = text
                    office_symbol_y = y
                elif self.SUBJECT_PATTERN.match(text) and not subject:
                    match = self.SUBJECT_PATTERN.match(text)
                    subject = match.group(2) if match else text
                    subject_y = y

            if office_symbol:
                header = ContinuationHeader(
                    office_symbol=office_symbol,
                    subject=subject or "",
                    page=page_num,
                    office_symbol_y=office_symbol_y,
                    subject_y=subject_y,
                )
                memo.continuation_headers.append(header)

    def _parse_page_numbers(self, memo: ParsedMemo) -> None:
        """Parse page numbers from each page."""
        for page_num in range(memo.page_count):
            page_lines = [line for line in self.lines if line.get("page") == page_num]

            for line in page_lines:
                text = line.get("text", "").strip()
                y = line.get("y_pos", 0)
                x = line.get("x_start", 0)

                # Page numbers are typically just digits near bottom
                if re.match(r"^\d+$", text) and len(text) <= 3 and y > 650:
                    memo.page_numbers[page_num] = {
                        "value": text,
                        "y": y,
                        "x": x,
                    }
                    break
