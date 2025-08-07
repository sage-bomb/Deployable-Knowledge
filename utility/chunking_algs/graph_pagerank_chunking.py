import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

from utility.model_utils import load_embedding_model


def safe_sent_tokenize(text: str):
    return re.split(r'(?<=[.!?]) +', text.strip())


def pagerank_chunk_text(
    text: str,
    model=None,
    sim_threshold: float = 0.5,
    top_k: int = 5,
    expansion_threshold: float = 0.5,
):
    sentences = safe_sent_tokenize(text)
    model = model or load_embedding_model()
    embeddings = model.encode(sentences, convert_to_tensor=False)

    sentence_ranges = []
    offset = 0
    for sent in sentences:
        start = text.find(sent, offset)
        end = start + len(sent)
        sentence_ranges.append((start, end))
        offset = end

    G = nx.Graph()
    sim_matrix = cosine_similarity(embeddings)
    for i in range(len(sentences)):
        G.add_node(i)
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            sim = sim_matrix[i][j]
            if sim > sim_threshold:
                G.add_edge(i, j, weight=sim)

    pageranks = nx.pagerank(G, weight="weight")
    seed_indices = sorted(pageranks, key=pageranks.get, reverse=True)[:top_k]

    used = set()
    chunks = []
    chunk_idx = 0
    for idx in seed_indices:
        if idx in used:
            continue
        chunk = [idx]
        used.add(idx)

        i = idx - 1
        while i >= 0 and i not in used and cosine_similarity(
            [embeddings[i]], [embeddings[chunk[0]]]
        )[0][0] > expansion_threshold:
            chunk.insert(0, i)
            used.add(i)
            i -= 1

        i = idx + 1
        while i < len(sentences) and i not in used and cosine_similarity(
            [embeddings[i]], [embeddings[chunk[-1]]]
        )[0][0] > expansion_threshold:
            chunk.append(i)
            used.add(i)
            i += 1

        chunk_text = " ".join(sentences[i] for i in chunk)
        start_char = sentence_ranges[chunk[0]][0]
        end_char = sentence_ranges[chunk[-1]][1]
        chunks.append(
            (
                chunk_text,
                {
                    "chunk_idx": chunk_idx,
                    "char_range": (start_char, end_char),
                    "num_sentences": len(chunk),
                },
            )
        )
        chunk_idx += 1

    return chunks
