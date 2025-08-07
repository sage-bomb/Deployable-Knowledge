from sklearn.metrics.pairwise import cosine_similarity
import re

from utility.model_utils import load_embedding_model


def embed(text, model):
    return model.encode([text])[0]


def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())


def cosine_sim(a, b):
    return cosine_similarity([a], [b])[0][0]


def recursive_split(chunk, model, min_similarity, max_depth=5, depth=0):
    if depth >= max_depth:
        return [chunk]
    sentences = safe_sent_tokenize(chunk)
    if len(sentences) <= 1:
        return [chunk]
    mid = len(sentences) // 2
    part1 = " ".join(sentences[:mid])
    part2 = " ".join(sentences[mid:])
    sim = cosine_sim(embed(part1, model), embed(part2, model))
    if sim < min_similarity:
        return recursive_split(part1, model, min_similarity, max_depth, depth + 1) + \
               recursive_split(part2, model, min_similarity, max_depth, depth + 1)
    return [chunk]


def merge_chunks(chunks, model, merge_threshold):
    merged = []
    i = 0
    any_merged = False
    while i < len(chunks):
        if i < len(chunks) - 1:
            sim = cosine_sim(embed(chunks[i], model), embed(chunks[i + 1], model))
            if sim > merge_threshold:
                merged.append(chunks[i] + " " + chunks[i + 1])
                i += 2
                any_merged = True
                continue
        merged.append(chunks[i])
        i += 1
    return merged, any_merged


def smart_chunk(text, model=None, min_split_similarity=0.8, merge_similarity=0.8, max_depth=5):
    model = model or load_embedding_model()
    split_chunks = []
    for chunk in [text]:
        split_chunks.extend(recursive_split(chunk, model, min_split_similarity, max_depth))
    merged_chunks, any_merged = merge_chunks(split_chunks, model, merge_similarity)
    if any_merged:
        final_chunks = []
        for chunk in merged_chunks:
            final_chunks.extend(recursive_split(chunk, model, min_split_similarity, max_depth=2))
    else:
        final_chunks = merged_chunks
    return final_chunks
