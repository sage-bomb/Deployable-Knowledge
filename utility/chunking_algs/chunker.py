from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer
import spacy
import pytextrank


import re

# NLTK hates human life and demands you all suffer at the hands of bad pickles.. all for the sake of a sentance spliter.
def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())

def chunk_by_sentences(sentences_with_page, max_chars=500):
    chunks = []
    current, current_pages = "", []
    chunk_idx = 0

    for sentence, page in sentences_with_page:
        if len(current) + len(sentence) < max_chars:
            current += " " + sentence
            current_pages.append(page)
        else:
            chunk_text = current.strip()
            chunks.append((chunk_text, {
                "chunk_idx": chunk_idx,
                "page": min(current_pages) if current_pages else None,
                "num_sentences": chunk_text.count('.') + chunk_text.count('!') + chunk_text.count('?')
            }))
            chunk_idx += 1
            current = sentence
            current_pages = [page]

    if current:
        chunk_text = current.strip()
        chunks.append((chunk_text, {
            "chunk_idx": chunk_idx,
            "page": min(current_pages) if current_pages else None,
            "num_sentences": chunk_text.count('.') + chunk_text.count('!') + chunk_text.count('?')
        }))

    return chunks


def chunk_by_semantic_similarity(sentences_with_page, model_name="all-MiniLM-L6-v2", threshold=0.6):
    model = SentenceTransformer(model_name)
    sentences = [s for s, _ in sentences_with_page]
    pages = [p for _, p in sentences_with_page]
    embeddings = model.encode(sentences, convert_to_tensor=True)

    chunks = []
    current_chunk, current_pages = [], []
    chunk_idx = 0

    for i in range(1, len(sentences)):
        current_chunk.append(sentences[i - 1])
        current_pages.append(pages[i - 1])
        sim = util.pytorch_cos_sim(embeddings[i - 1], embeddings[i]).item()
        if sim < threshold:
            chunk_text = " ".join(current_chunk)
            chunks.append((chunk_text.strip(), {
                "chunk_idx": chunk_idx,
                "page": min(current_pages),
                "semantic_break": True
            }))
            chunk_idx += 1
            current_chunk, current_pages = [], []

    current_chunk.append(sentences[-1])
    current_pages.append(pages[-1])
    chunk_text = " ".join(current_chunk)
    chunks.append((chunk_text.strip(), {
        "chunk_idx": chunk_idx,
        "page": min(current_pages),
        "semantic_break": False
    }))
    return chunks

def split_text_by_length(text, max_chars=100000):
    """
    Split text into chunks <= max_chars characters, preferably at paragraph breaks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            newline_idx = text.rfind("\n\n", start, end)
            if newline_idx != -1 and newline_idx > start:
                end = newline_idx + 2
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks


def chunk_by_graph_rank(text, max_sentences=4):
    nlp = spacy.load("en_core_web_trf")
    nlp.add_pipe("textrank", last=True)  # Ensure PyTextRank is applied
    nlp.max_length = 2_000_000  # Optional: Increase limit if you're confident in memory

    text_chunks = split_text_by_length(text, max_chars=500_000)  # Safe size
    all_chunks = []
    chunk_idx = 0
    global_offset = 0  # Tracks position within the full text

    for subtext in text_chunks:
        doc = nlp(subtext)
        current, char_offset = [], 0

        for sent in doc.sents:
            current.append(sent.text)
            if len(current) >= max_sentences:
                chunk_text = " ".join(current)
                start_in_full_text = text.find(chunk_text, global_offset)

                all_chunks.append((
                    chunk_text.strip(),
                    {
                        "chunk_idx": chunk_idx,
                        "char_range": (start_in_full_text, start_in_full_text + len(chunk_text)),
                        "num_sentences": len(current)
                    }
                ))

                global_offset = start_in_full_text + len(chunk_text)
                chunk_idx += 1
                current = []

        if current:
            chunk_text = " ".join(current)
            start_in_full_text = text.find(chunk_text, global_offset)

            all_chunks.append((
                chunk_text.strip(),
                {
                    "chunk_idx": chunk_idx,
                    "char_range": (start_in_full_text, start_in_full_text + len(chunk_text)),
                    "num_sentences": len(current)
                }
            ))

            chunk_idx += 1
            global_offset = start_in_full_text + len(chunk_text)

    return all_chunks

def safe_chunk_by_graph_rank(sentences_with_page, max_sentences=4, max_tokens_per_chunk=256, model_name="all-MiniLM-L6-v2"):
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2_000_000
    nlp.add_pipe("textrank", last=True)

    model = SentenceTransformer(model_name)
    tokenizer = model.tokenizer

    chunks = []
    chunk_idx = 0
    current_sentences = []
    current_pages = []

    def flush_chunk():
        nonlocal chunk_idx, current_sentences, current_pages
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            page = min(current_pages) if current_pages else None
            chunks.append((
                chunk_text.strip(),
                {
                    "chunk_idx": chunk_idx,
                    "page": page,
                    "num_sentences": len(current_sentences)
                }
            ))
            chunk_idx += 1
            current_sentences = []
            current_pages = []

    for (sent_text, page) in sentences_with_page:
        token_ids = tokenizer.encode(sent_text, truncation=True)

        if len(token_ids) > max_tokens_per_chunk:
            token_ids = token_ids[:max_tokens_per_chunk]
            sent_text = tokenizer.decode(token_ids, skip_special_tokens=True)

        current_sentences.append(sent_text)
        current_pages.append(page)

        joined = " ".join(current_sentences)
        joined_token_ids = tokenizer.encode(joined, truncation=False)

        if len(current_sentences) >= max_sentences or len(joined_token_ids) >= max_tokens_per_chunk:
            flush_chunk()

    flush_chunk()
    return chunks


def chunk_by_paragraphs(text, page_aware_sentences, model_name="all-MiniLM-L6-v2", threshold=0.7):
    model = SentenceTransformer(model_name)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    embeddings = model.encode(paragraphs, convert_to_tensor=True)

    chunks, current, current_pages = [], [], []
    chunk_idx = 0

    # map each paragraph to its most common page number based on sentences
    para_pages = []
    for para in paragraphs:
        para_sents = [page for sent, page in page_aware_sentences if sent in para]
        para_pages.append(min(para_sents) if para_sents else None)

    for i in range(1, len(paragraphs)):
        current.append(paragraphs[i - 1])
        current_pages.append(para_pages[i - 1])
        sim = util.pytorch_cos_sim(embeddings[i - 1], embeddings[i]).item()
        if sim < threshold:
            chunk_text = "\n\n".join(current)
            chunks.append((chunk_text.strip(), {
                "chunk_idx": chunk_idx,
                "page": min(current_pages),
                "semantic_gap": True
            }))
            chunk_idx += 1
            current, current_pages = [], []

    current.append(paragraphs[-1])
    current_pages.append(para_pages[-1])
    chunk_text = "\n\n".join(current)
    chunks.append((chunk_text.strip(), {
        "chunk_idx": chunk_idx,
        "page": min(current_pages),
        "semantic_gap": False
    }))
    return chunks
