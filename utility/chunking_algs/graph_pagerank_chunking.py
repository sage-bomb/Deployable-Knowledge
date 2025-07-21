import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import re

def sentence_tokenize_with_page(text_by_page):
    """
    Given a list of {"page": int, "text": str}, return
    List of (sentence, page) pairs.
    """
    pattern = r'(?<=[.!?])\s+'
    result = []

    for page_data in text_by_page:
        page = page_data["page"]
        raw_text = page_data["text"].strip()
        sentences = re.split(pattern, raw_text)
        for s in sentences:
            sentence = s.strip()
            if sentence:
                result.append((sentence, page))
    return result
def pagerank_chunk_text(text_by_page, model_name="all-mpnet-base-v2", sim_threshold=0.7, expansion_threshold=0.5):
    """
    Text-by-page version that avoids char_range, tracks page per sentence.
    """
    sentence_page_pairs = sentence_tokenize_with_page(text_by_page)
    if not sentence_page_pairs:
        return []

    sentences = [s for s, _ in sentence_page_pairs]
    sentence_pages = [pg for _, pg in sentence_page_pairs]

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

        new_chunk = " ".join([sentences[i] for i in chunk])
        # Choose page number of the first sentence in chunk
        page_number = sentence_pages[chunk[0]]

        chunks.append((
            new_chunk,
            {
                "chunk_idx": chunk_idx,
                "page": page_number,
                "num_sentences": len(chunk)
            }
        ))
        chunk_idx += 1


    return chunks