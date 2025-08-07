from sklearn.metrics.pairwise import cosine_similarity
import re

from utility.model_utils import load_embedding_model


def embed(text, model):
    return model.encode([text])[0]


def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())


def merge_sentences_bottom_up(text, similarity_threshold=0.7, model=None):
    model = model or load_embedding_model()
    sentences = safe_sent_tokenize(text)
    chunks = sentences[:]
    embeddings = [embed(s, model) for s in chunks]

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
                    merged_chunk = chunks[i] + " " + chunks[i + 1]
                    new_chunks.append(merged_chunk)
                    new_embeddings.append(embed(merged_chunk, model))
                    i += 2
                    merged = True
                    continue
            new_chunks.append(chunks[i])
            new_embeddings.append(embeddings[i])
            i += 1
        chunks, embeddings = new_chunks, new_embeddings

    final_chunks = []
    for idx, chunk in enumerate(chunks):
        start = text.find(chunk)
        final_chunks.append(
            (
                chunk,
                {
                    "chunk_idx": idx,
                    "char_range": (start, start + len(chunk)),
                    "num_sentences": chunk.count('.') + chunk.count('!') + chunk.count('?'),
                },
            )
        )
    return final_chunks
