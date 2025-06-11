import pdfplumber
from pathlib import Path

def parse_pdf(pdf_path, margin_top=50, margin_bottom=50, margin_left=50, margin_right=50):
    """
    Extracts clean text from a PDF, removing headers and footers based on layout.
    Adapts to portrait and landscape orientation by checking page rotation/shape.
    """
    pdf_path = Path(pdf_path)
    assert pdf_path.exists(), f"File does not exist: {pdf_path}"

    all_cleaned_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue

            is_landscape = page.width > page.height or page.rotation in [90, 270]

            cleaned_words = []
            for word in words:
                # margin information
                # print(f"{word['text']:30} top: {word['top']:.1f} bottom: {word['bottom']:.1f}")
                if is_within_margins(word, page, is_landscape, margin_top, margin_bottom, margin_left, margin_right):
                    key = word['x0'] if is_landscape else word['top']
                    cleaned_words.append((key, word['text']))
                else:
                    #testing margin work
                    print(f"Skipping word '{word['text']}' at {word['x0'] if is_landscape else word['top']} due to margin constraints.")

            # Sort words by vertical (portrait) or horizontal (landscape) position
            cleaned_words.sort(key=lambda x: x[0])
            grouped_lines = group_words_by_line(cleaned_words, is_landscape)
            all_cleaned_text.append("\n".join(grouped_lines))

    return "\n\n".join(all_cleaned_text)


def is_within_margins(word, page, is_landscape, margin_top, margin_bottom, margin_left, margin_right):
    """
    Return True if the word is not within the margin zones.
    - Portrait: uses top/bottom
    - Landscape: uses x0/x1
    """
    if is_landscape:
        return (
            margin_left < word['x0'] < (page.width - margin_right)
        )
    else:
        return (
            margin_top < word['top'] < (page.height - margin_bottom)
        )


def group_words_by_line(words_with_key, is_landscape, line_tol=5):
    """
    Groups words into lines by vertical (portrait) or horizontal (landscape) proximity.
    """
    lines = []
    current_line = []
    current_key = None

    for key, word in words_with_key:
        if current_key is None or abs(key - current_key) <= line_tol:
            current_line.append(word)
            if current_key is None:
                current_key = key
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_key = key

    if current_line:
        lines.append(" ".join(current_line))

    return lines


# Replace input_pdf and output_txt with desired file paths
if __name__ == "__main__":
    input_pdf = "cisco_test.pdf"
    output_txt = "parsed.txt"

    # Typically margins are 1-inch, which is 72 points for PDF
    cleaned_text = parse_pdf(
        input_pdf,
        margin_top=120,
        margin_bottom=120,
        margin_left=50,
        margin_right=50
    )

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"Extracted text saved to {output_txt}")

# cisco_test.pdf header and footer notes
# footer for portrait view: top: 676.3 bottom: 685.3