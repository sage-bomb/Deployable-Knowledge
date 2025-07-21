from sentence_transformers import SentenceTransformer, util
import spacy
import pytextrank


import re

# NLTK hates human life and demands you all suffer at the hands of bad pickles.. all for the sake of a sentance spliter.
def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())

def chunk_by_sentences(text, max_chars=500):
    sentences = safe_sent_tokenize(text)  # <- no nltk here

    chunks = []
    current, start_char, chunk_idx = "", 0, 0

    for sent in sentences:
        if len(current) + len(sent) < max_chars:
            current += " " + sent
        else:
            chunk_text = current.strip()
            chunks.append((chunk_text, {
                "chunk_idx": chunk_idx,
                "start_char": start_char,
                "num_sentences": chunk_text.count('.') + chunk_text.count('!') + chunk_text.count('?')
            }))
            chunk_idx += 1
            start_char += len(chunk_text)
            current = sent

    if current:
        chunk_text = current.strip()
        chunks.append((chunk_text, {
            "chunk_idx": chunk_idx,
            "start_char": start_char,
            "num_sentences": chunk_text.count('.') + chunk_text.count('!') + chunk_text.count('?')
        }))
    return chunks


def chunk_by_semantic_similarity(text, model_name="all-MiniLM-L6-v2", threshold=0.6):
    model = SentenceTransformer(model_name)
    sentences = safe_sent_tokenize(text)
    embeddings = model.encode(sentences, convert_to_tensor=True)

    chunks = []
    current_chunk, start_char, chunk_idx = [], 0, 0

    for i in range(1, len(sentences)):
        current_chunk.append(sentences[i-1])
        sim = util.pytorch_cos_sim(embeddings[i-1], embeddings[i]).item()
        if sim < threshold:
            chunk_text = " ".join(current_chunk)
            chunks.append((chunk_text.strip(), {
                "chunk_idx": chunk_idx,
                "start_char": text.find(chunk_text),
                "semantic_break": True
            }))
            chunk_idx += 1
            current_chunk = []

    current_chunk.append(sentences[-1])
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append((chunk_text.strip(), {
            "chunk_idx": chunk_idx,
            "start_char": text.find(chunk_text),
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

def safe_chunk_by_graph_rank(text, max_sentences=4, max_tokens_per_chunk=256, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    # Load and configure spaCy pipeline
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2_000_000
    nlp.add_pipe("textrank", last=True)
    tokenizer = SentenceTransformer(model_name).tokenizer

    # Optional: break very large input into subchunks to keep memory/token safe
    def split_text_by_length(text, max_tokens=2000):
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + max_tokens]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            i += max_tokens
        return chunks

    all_chunks = []
    chunk_idx = 0
    global_offset = 0

    for subtext in split_text_by_length(text, max_tokens=2000):
        doc = nlp(subtext)
        current_sentences = []
        for sent in doc.sents:
            sent_text = sent.text
            sent_tokens = tokenizer.encode(sent_text, truncation=True)

            if len(sent_tokens) > max_tokens_per_chunk:
                # Too long — truncate at the sentence level
                sent_tokens = sent_tokens[:max_tokens_per_chunk]
                sent_text = tokenizer.decode(sent_tokens, skip_special_tokens=True)

            current_sentences.append(sent_text)

            joined = " ".join(current_sentences)
            joined_tokens = tokenizer.encode(joined, truncation=False)

            if len(current_sentences) >= max_sentences or len(joined_tokens) >= max_tokens_per_chunk:
                chunk_text = " ".join(current_sentences)
                start = text.find(chunk_text, global_offset)

                all_chunks.append((
                    chunk_text.strip(),
                    {
                        "chunk_idx": chunk_idx,
                        "char_range": (start, start + len(chunk_text)),
                        "num_sentences": len(current_sentences),
                    }
                ))

                global_offset = start + len(chunk_text)
                chunk_idx += 1
                current_sentences = []

        # Add remaining
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            start = text.find(chunk_text, global_offset)
            all_chunks.append((
                chunk_text.strip(),
                {
                    "chunk_idx": chunk_idx,
                    "char_range": (start, start + len(chunk_text)),
                    "num_sentences": len(current_sentences),
                }
            ))
            chunk_idx += 1
            global_offset = start + len(chunk_text)

    return all_chunks

def chunk_by_paragraphs(text, model_name="all-MiniLM-L6-v2", threshold=0.7):
    model = SentenceTransformer(model_name)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    embeddings = model.encode(paragraphs, convert_to_tensor=True)

    chunks, current, chunk_idx = [], [], 0
    char_offset = 0

    for i in range(1, len(paragraphs)):
        current.append(paragraphs[i-1])
        sim = util.pytorch_cos_sim(embeddings[i-1], embeddings[i]).item()
        if sim < threshold:
            chunk_text = "\n\n".join(current)
            chunks.append((chunk_text.strip(), {
                "chunk_idx": chunk_idx,
                "start_char": text.find(chunk_text, char_offset),
                "semantic_gap": True
            }))
            char_offset += len(chunk_text)
            chunk_idx += 1
            current = []

    current.append(paragraphs[-1])
    if current:
        chunk_text = "\n\n".join(current)
        chunks.append((chunk_text.strip(), {
            "chunk_idx": chunk_idx,
            "start_char": text.find(chunk_text, char_offset),
            "semantic_gap": False
        }))
    return chunks
