from pathlib import Path
from typing import List, Dict
import pdfplumber


class PDFPlumberOCR:
    def __init__(
            self,
            margin_top: int = 50,
            margin_bottom: int = 50,
            margin_left: int = 50,
            margin_right: int = 50,
            line_tol: int = 5
    ):
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.line_tol = line_tol
    
    def parse_pdf(self, pdf_path: Path) -> List[str]:
        """
        Extracts clean text from a PDF, removing headers and footers based on layout.
        Adapts to portrait and landscape orientation by checking page rotation/shape.
        Returns a list of joined lines of text for each page.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"File does not exist: {pdf_path}")
        
        page_texts = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                
                is_landscape = page.width > page.height
                words = page.extract_words()

                #filtering out content in the margins
                cleaned_words = [
                    word for word in words
                    if self.is_within_margins(word, page, is_landscape)
                ]

                #grouping words by line
                lines = self.group_words_by_line(cleaned_words, is_landscape)
                joined_lines = "\n".join(" ".join(word["text"] for word in line) for line in lines)
                page_texts.append(joined_lines.strip())
        
        return page_texts
    
    def is_within_margins(
            self,
            word: Dict,
            page,
            is_landscape: bool
    ) -> bool:
        """
        Return True if the word is not within the margin zones.
        Portrait uses vertical margins, Landscape uses horizontal margins.
        """
        if is_landscape:
            x0, x1 = word['x0'], word['x1']
            return (x0 > self.margin_left) and (x1 < page.width - self.margin_right)
        else:
            top, bottom = word['top'], word['bottom']
            return (top > self.margin_top) and (bottom < page.height - self.margin_bottom)
    
    def group_words_by_line(
            self,
            words: List[Dict],
            is_landscape: bool
    ) -> List[List[Dict]]:
        """
        Groups words into lines by recognized orientation.
        Returns a list of lines, each line being a list of words dicts
        """

        if not words:
            return []
        
        key = "top" if not is_landscape else "x0"
        sorted_words = sorted(words, key=lambda w: w[key])

        lines = []
        current_line = [sorted_words[0]]

        for word in sorted_words[1:]:
            prev = current_line[-1]
            distance = abs(word[key] - prev[key])
            if distance <= self.line_tol:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        lines.append(current_line)  # Add the last line
        return lines
    
    def save_text_to_file(self, pdf_path: Path, output_path: Path):
        """
        Saves the parsed pdf text (one page per block) to a plain txt file
        """
        parsed_text = self.parse_pdf(pdf_path)

        with output_path.open("w", encoding="utf-8") as f:
            for i, page_text in enumerate(parsed_text):
                f.write(f"Page {i + 1}---\n")
                f.write(page_text + "\n\n")