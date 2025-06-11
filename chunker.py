import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util
import spacy
import pytextrank

nltk.download('punkt')

def chunk_by_sentences(text, max_chars=500):
    sentences = sent_tokenize(text)
    chunks = []
    current, start_char, chunk_idx = "", 0, 0

    for sent in sentences:
        if len(current) + len(sent) < max_chars:
            current += " " + sent
        else:
            chunks.append((current.strip(), {
                "chunk_idx": chunk_idx,
                "start_char": start_char,
                "num_sentences": current.count('.') + current.count('!') + current.count('?')
            }))
            chunk_idx += 1
            start_char += len(current)
            current = sent

    if current:
        chunks.append((current.strip(), {
            "chunk_idx": chunk_idx,
            "start_char": start_char,
            "num_sentences": current.count('.') + current.count('!') + current.count('?')
        }))
    return chunks

def chunk_by_semantic_similarity(text, model_name="all-MiniLM-L6-v2", threshold=0.6):
    model = SentenceTransformer(model_name)
    sentences = sent_tokenize(text)
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

def chunk_by_graph_rank(text, max_sentences=4):
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("textrank")  # PyTextRank modifies the doc with sentence ranking

    doc = nlp(text)
    chunks, current, chunk_idx = [], [], 0
    char_offset = 0

    for sent in doc.sents:
        current.append(sent.text)
        if len(current) >= max_sentences:
            chunk_text = " ".join(current)
            chunks.append((chunk_text.strip(), {
                "chunk_idx": chunk_idx,
                "start_char": text.find(chunk_text, char_offset),
                "num_sentences": len(current)
            }))
            char_offset += len(chunk_text)
            chunk_idx += 1
            current = []

    if current:
        chunk_text = " ".join(current)
        chunks.append((chunk_text.strip(), {
            "chunk_idx": chunk_idx,
            "start_char": text.find(chunk_text, char_offset),
            "num_sentences": len(current)
        }))
    return chunks

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
