import pdfplumber
from pathlib import Path
import argparse
from collections import Counter

def remove_frequent_lines(pages, threshold=0.9):
    """
    Remove lines that appear in more than `threshold` proportion of pages.
    """
    all_lines = [line.strip() for page in pages for line in page["text"].split("\n") if line.strip()]
    line_counts = Counter(all_lines)
    total_pages = len(pages)
    common_lines = {
        line for line, count in line_counts.items()
        if count / total_pages > threshold
    }

    filtered_pages = []
    for page in pages:
        lines = page["text"].split("\n")
        filtered_lines = [line for line in lines if line.strip() not in common_lines]
        filtered_pages.append({
            "page": page["page"],
            "text": "\n".join(filtered_lines)
        })
    return filtered_pages

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
                    #print(f"Skipping word '{word['text']}' at {word['x0'] if is_landscape else word['top']} due to margin constraints.")
                    continue

            # Sort words by vertical (portrait) or horizontal (landscape) position
            cleaned_words.sort(key=lambda x: x[0])
            grouped_lines = group_words_by_line(cleaned_words, is_landscape)
            all_cleaned_text.append({
            "page": page_idx + 1,
            "text": "\n".join(grouped_lines)
        })

    all_cleaned_text = remove_frequent_lines(all_cleaned_text)  # update this function if needed

    return all_cleaned_text


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
    parser = argparse.ArgumentParser(description="Extract clean text from a PDF, removing headers and footers.")
    parser.add_argument("input_pdf", type=str, help="Path to the input PDF file")
    parser.add_argument("output_txt", type=str, help="Path to the output text file")
    parser.add_argument("--margin_top", type=int, default=50, help="Top margin in points (default: 50)")
    parser.add_argument("--margin_bottom", type=int, default=50, help="Bottom margin in points (default: 50)")
    parser.add_argument("--margin_left", type=int, default=50, help="Left margin in points (default: 50)")
    parser.add_argument("--margin_right", type=int, default=50, help="Right margin in points (default: 50)")

    args = parser.parse_args()

    cleaned_text = parse_pdf(
        args.input_pdf,
        margin_top=args.margin_top,
        margin_bottom=args.margin_bottom,
        margin_left=args.margin_left,
        margin_right=args.margin_right
    )

    output_path = Path(args.output_txt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    full_text = "\n\n".join(page["text"] for page in cleaned_text)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Extracted text saved to {output_path}")
