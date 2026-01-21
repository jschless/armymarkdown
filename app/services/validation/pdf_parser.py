"""
PDF parsing service for extracting text, fonts, and margins from Army memorandum PDFs.

Uses pdfplumber for text and layout extraction to enable AR 25-50 compliance checking.
"""

from dataclasses import dataclass, field
from io import BytesIO

import pdfplumber


@dataclass
class PDFMetadata:
    """Extracted metadata from a PDF document."""

    text_content: str = ""
    fonts: list[dict] = field(default_factory=list)
    margins: dict = field(default_factory=dict)
    page_count: int = 0
    extraction_errors: list[str] = field(default_factory=list)
    # Line data for indentation analysis: [{text, x_start, y_pos, page}]
    lines: list[dict] = field(default_factory=list)


class PDFParser:
    """Parse PDF documents to extract content and formatting metadata."""

    # Standard page dimensions in points (8.5 x 11 inches at 72 dpi)
    PAGE_WIDTH_POINTS = 612  # 8.5 inches * 72 dpi
    PAGE_HEIGHT_POINTS = 792  # 11 inches * 72 dpi

    # Standard margin in points (1 inch = 72 points)
    STANDARD_MARGIN_POINTS = 72

    def parse(self, pdf_bytes: bytes) -> PDFMetadata:
        """
        Parse a PDF document from bytes.

        Args:
            pdf_bytes: Raw PDF file content as bytes

        Returns:
            PDFMetadata containing extracted text, fonts, margins, and page count
        """
        metadata = PDFMetadata()

        try:
            pdf_stream = BytesIO(pdf_bytes)
            with pdfplumber.open(pdf_stream) as pdf:
                metadata.page_count = len(pdf.pages)

                # Extract content from all pages
                all_text = []
                all_fonts = {}
                margin_measurements = []
                all_lines = []

                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text() or ""
                    all_text.append(page_text)

                    # Extract font information from characters
                    chars = page.chars or []
                    for char in chars:
                        font_name = char.get("fontname", "Unknown")
                        font_size = round(char.get("size", 0), 1)
                        font_key = f"{font_name}|{font_size}"

                        if font_key not in all_fonts:
                            all_fonts[font_key] = {
                                "name": font_name,
                                "size": font_size,
                                "count": 0,
                            }
                        all_fonts[font_key]["count"] += 1

                    # Extract line position data for indentation analysis
                    page_lines = self._extract_lines(chars, page_num)
                    all_lines.extend(page_lines)

                    # Calculate margins from character bounding boxes
                    page_margins = self._calculate_page_margins(page)
                    if page_margins:
                        margin_measurements.append(page_margins)

                # Combine all text content
                metadata.text_content = "\n\n".join(all_text)

                # Convert fonts dict to list sorted by frequency
                metadata.fonts = sorted(
                    all_fonts.values(), key=lambda x: x["count"], reverse=True
                )

                # Average margins across all pages
                metadata.margins = self._average_margins(margin_measurements)

                # Store line data for indentation analysis
                metadata.lines = all_lines

        except Exception as e:
            metadata.extraction_errors.append(f"PDF parsing error: {e!s}")

        return metadata

    def _calculate_page_margins(self, page) -> dict | None:
        """
        Calculate margins from character/object positions on a page.

        Args:
            page: pdfplumber Page object

        Returns:
            Dictionary with margin measurements in inches, or None if unable to calculate
        """
        chars = page.chars or []
        if not chars:
            return None

        # Get page dimensions
        page_width = page.width or self.PAGE_WIDTH_POINTS
        page_height = page.height or self.PAGE_HEIGHT_POINTS

        # Find content boundaries
        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")

        for char in chars:
            x0 = char.get("x0", 0)
            x1 = char.get("x1", 0)
            top = char.get("top", 0)
            bottom = char.get("bottom", 0)

            min_x = min(min_x, x0)
            max_x = max(max_x, x1)
            min_y = min(min_y, top)
            max_y = max(max_y, bottom)

        if min_x == float("inf") or max_x == float("-inf"):
            return None

        # Calculate margins in points, then convert to inches
        left_margin_points = min_x
        right_margin_points = page_width - max_x
        top_margin_points = min_y
        bottom_margin_points = page_height - max_y

        return {
            "left": round(left_margin_points / 72, 2),
            "right": round(right_margin_points / 72, 2),
            "top": round(top_margin_points / 72, 2),
            "bottom": round(bottom_margin_points / 72, 2),
        }

    def _average_margins(self, margin_list: list[dict]) -> dict:
        """
        Calculate average margins from multiple pages.

        Args:
            margin_list: List of margin dictionaries from each page

        Returns:
            Dictionary with averaged margin values
        """
        if not margin_list:
            return {"left": 0, "right": 0, "top": 0, "bottom": 0}

        avg_margins = {"left": 0, "right": 0, "top": 0, "bottom": 0}

        for margins in margin_list:
            for key in avg_margins:
                avg_margins[key] += margins.get(key, 0)

        count = len(margin_list)
        for key in avg_margins:
            avg_margins[key] = round(avg_margins[key] / count, 2)

        return avg_margins

    def _extract_lines(self, chars: list, page_num: int) -> list[dict]:
        """
        Extract line data from characters for indentation analysis.

        Groups characters by their vertical position (line) and returns
        text content with x-position for each line.

        Args:
            chars: List of character dictionaries from pdfplumber
            page_num: Page number (0-indexed)

        Returns:
            List of line dictionaries with text, x_start, y_pos, page
        """
        if not chars:
            return []

        # Group characters by line (using top position, rounded to handle minor variations)
        line_groups = {}
        for char in chars:
            # Round y position to group characters on same line (within 2 points)
            y_key = round(char.get("top", 0) / 2) * 2
            if y_key not in line_groups:
                line_groups[y_key] = []
            line_groups[y_key].append(char)

        lines = []
        for y_pos in sorted(line_groups.keys()):
            line_chars = line_groups[y_pos]
            # Sort characters by x position
            line_chars.sort(key=lambda c: c.get("x0", 0))

            # Build text and get starting x position
            text = "".join(c.get("text", "") for c in line_chars)
            x_start = line_chars[0].get("x0", 0) if line_chars else 0

            lines.append(
                {
                    "text": text,
                    "x_start": round(x_start, 1),
                    "y_pos": round(y_pos, 1),
                    "page": page_num,
                }
            )

        return lines

    def is_likely_image_pdf(self, metadata: PDFMetadata) -> bool:
        """
        Check if the PDF appears to be a scanned/image-based document.

        Args:
            metadata: Extracted PDF metadata

        Returns:
            True if the PDF likely contains no extractable text (scanned document)
        """
        # If we have pages but very little text, it's likely scanned
        if metadata.page_count > 0:
            text_per_page = len(metadata.text_content) / metadata.page_count
            # Typical memo page has at least 500 characters
            return text_per_page < 100

        return False
