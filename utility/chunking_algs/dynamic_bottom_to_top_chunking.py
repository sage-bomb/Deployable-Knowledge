# Updated bottom-up merging chunker to support (sentence, page_num) inputs
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())


def embed(text, model):
    return model.encode([text])[0]


def merge_sentences_bottom_up(text, similarity_threshold, model_name="all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)

    # Split into sentences and assign dummy page number (used if no page mapping provided)
    raw_sentences = safe_sent_tokenize(text)
    sentence_page_pairs = [(sent, None) for sent in raw_sentences]

    return merge_bottom_up_with_pages(sentence_page_pairs, similarity_threshold, model)


def merge_bottom_up_with_pages(sentence_page_pairs, similarity_threshold=0.7, model=None):
    if model is None:
        model = SentenceTransformer("all-mpnet-base-v2")

    chunks = sentence_page_pairs[:]
    embeddings = [embed(s, model) for s, _ in chunks]

    merged = True
    while merged and len(chunks) > 1:
        merged = False
        new_chunks = []
        new_embeddings = []
        i = 0
        while i < len(chunks):
            if i < len(chunks) - 1:
                sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
                if sim > similarity_threshold:
                    merged_text = chunks[i][0] + " " + chunks[i + 1][0]
                    merged_page = chunks[i][1]  # retain page of first
                    merged_chunk = (merged_text, merged_page)
                    new_chunks.append(merged_chunk)
                    new_embeddings.append(embed(merged_text, model))
                    i += 2
                    merged = True
                    continue
            new_chunks.append(chunks[i])
            new_embeddings.append(embeddings[i])
            i += 1
        chunks = new_chunks
        embeddings = new_embeddings

    # Package final output as (chunk_text, metadata)
    output = []
    for idx, (chunk_text, page) in enumerate(chunks):
        output.append((chunk_text, {
            "chunk_idx": idx,
            "page": page,
            "num_sentences": chunk_text.count('.') + chunk_text.count('!') + chunk_text.count('?')
        }))

    return output