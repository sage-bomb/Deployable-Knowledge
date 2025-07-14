import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import re

def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())

def pagerank_chunk_text(text, model_name="all-mpnet-base-v2", sim_threshold=0.5, top_k=5, expansion_threshold=0.5):
    # ---- STEP 1: Preprocessing ----
    sentences = safe_sent_tokenize(text)
    model = SentenceTransformer(model_name)
    embeddings = model.encode(sentences, convert_to_tensor=False)

    # ---- STEP 2: Build Similarity Graph ----
    G = nx.Graph()
    sim_matrix = cosine_similarity(embeddings)

    for i, sentence in enumerate(sentences):
        G.add_node(i, text=sentence)

    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            sim = sim_matrix[i][j]
            if sim > sim_threshold:
                G.add_edge(i, j, weight=sim)

    # ---- STEP 3: Compute PageRank ----
    pageranks = nx.pagerank(G, weight='weight')

    # ---- STEP 4: Seeded Expansion ----
    seed_indices = sorted(pageranks, key=pageranks.get, reverse=True)
    used = set()
    chunks = []
    chunk_idx=0

    for idx in seed_indices:
        if idx in used:
            continue

        chunk = [idx]
        used.add(idx)

        # Expand to the left
        i = idx - 1
        while i >= 0 and i not in used and cosine_similarity([embeddings[i]], [embeddings[chunk[0]]])[0][0] > expansion_threshold:
            chunk.insert(0, i)
            used.add(i)
            i -= 1

        # Expand to the right
        i = idx + 1
        while i < len(sentences) and i not in used and cosine_similarity([embeddings[i]], [embeddings[chunk[-1]]])[0][0] > expansion_threshold:
            chunk.append(i)
            used.add(i)
            i += 1

        new_chunk=" ".join([sentences[i] for i in chunk])
        start = text.find(new_chunk)
        chunks.append(new_chunk, {
            "chunk_idx": chunk_idx,
            "char_range": (start, start + len(new_chunk)),
            "num_sentences": new_chunk.count('.') + new_chunk.count('!') + new_chunk.count('?')
        })
        chunk_idx=chunk_idx+1


    return chunks