# This chunking 

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

model = SentenceTransformer('all-MiniLM-L6-v2')

def pre_split_lines_as_paragraphs(text, max_lines=6):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    grouped = []
    for i in range(0, len(lines), max_lines):
        group = " ".join(lines[i:i + max_lines])
        grouped.append(group)
    return grouped

def embed(text):
    return model.encode([text])[0]

def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())

def cosine_sim(a, b):
    return cosine_similarity([a], [b])[0][0]

def recursive_split(chunk, min_similarity, max_depth=5, depth=0):
    if depth >= max_depth:
        return [chunk]
    
    sentences = safe_sent_tokenize(chunk)
    if len(sentences) <= 1:
        return [chunk]
    
    mid = len(sentences) // 2
    part1 = " ".join(sentences[:mid])
    part2 = " ".join(sentences[mid:])

    sim = cosine_sim(embed(part1), embed(part2))
    
    if sim < min_similarity:
        return (
            recursive_split(part1, min_similarity, max_depth, depth + 1) +
            recursive_split(part2, min_similarity, max_depth, depth + 1)
        )
    else:
        return [chunk]

def merge_chunks(chunks, merge_threshold):
    merged = []
    i = 0
    any_merged = False  # Track if any merging happened

    while i < len(chunks):
        if i < len(chunks) - 1:
            sim = cosine_sim(embed(chunks[i]), embed(chunks[i+1]))
            if sim > merge_threshold:
                merged_chunk = chunks[i] + " " + chunks[i+1]
                merged.append(merged_chunk)
                i += 2
                any_merged = True
                continue
        merged.append(chunks[i])
        i += 1
    return merged, any_merged

def smart_chunk(text, min_split_similarity=0.8, merge_similarity=0.8, max_depth=5):
    # Step 1: Initial recursive split
    initial_chunks = [text]#pre_split_lines_as_paragraphs(text)
    split_chunks = []
    for chunk in initial_chunks:
        split_chunks.extend(recursive_split(chunk, min_split_similarity, max_depth))

    # Step 2: Merge adjacent chunks
    merged_chunks, any_merged = merge_chunks(split_chunks, merge_similarity)

    # Step 3: If any merges occurred, re-check those merged chunks
    if any_merged:
        final_chunks = []
        for chunk in merged_chunks:
            final_chunks.extend(recursive_split(chunk, min_split_similarity, max_depth=2))
    else:
        final_chunks = merged_chunks

    return final_chunks