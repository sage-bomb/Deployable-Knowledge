from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
nltk.download("punkt")
from nltk.tokenize import sent_tokenize
import numpy as np
import re

def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())

def embed_sentences(sentences, model):
    return model.encode(sentences)

def semantic_chunking(sentences, embeddings, similarity_threshold=0.75):
    chunks = []
    current_chunk = [sentences[0]]
    last_embedding = embeddings[0].reshape(1, -1)

    for i in range(1, len(sentences)):
        curr_embedding = embeddings[i].reshape(1, -1)
        similarity = cosine_similarity(last_embedding, curr_embedding)[0][0]

        if similarity >= similarity_threshold:
            current_chunk.append(sentences[i])
        else:
            chunks.append(current_chunk)
            current_chunk = [sentences[i]]
        last_embedding = curr_embedding

    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def mean_embedding(embeddings):
    return np.mean(embeddings, axis=0)

def recursive_split(sentences, embeddings, model, max_tokens=200, similarity_threshold=0.7):
    # Base case: small chunk or few sentences
    if len(sentences) <= 1:
        return [" ".join(sentences)]

    # Approximate token count (assuming avg 1.3 tokens per word)
    token_count = sum(len(s.split()) for s in sentences)

    # Calculate similarity between halves
    mid = len(sentences) // 2
    left_embed = mean_embedding(embeddings[:mid]).reshape(1, -1)
    right_embed = mean_embedding(embeddings[mid:]).reshape(1, -1)
    similarity = cosine_similarity(left_embed, right_embed)[0][0]

    # If chunk is too large or similarity is low, split recursively
    if token_count > max_tokens or similarity < similarity_threshold:
        left_chunks = recursive_split(sentences[:mid], embeddings[:mid], model, max_tokens, similarity_threshold)
        right_chunks = recursive_split(sentences[mid:], embeddings[mid:], model, max_tokens, similarity_threshold)
        return left_chunks + right_chunks
    else:
        return [" ".join(sentences)]

def semantic_recursive_chunking(text, model_name="all-mpnet-base-v2",
                               initial_similarity_threshold=0.75,
                               recursive_similarity_threshold=0.7,
                               max_tokens=200):
    model = SentenceTransformer(model_name)
    sentences = safe_sent_tokenize(text)
    embeddings = embed_sentences(sentences, model)

    # Step 1: Initial semantic chunking by sentence similarity
    initial_chunks = semantic_chunking(sentences, embeddings, similarity_threshold=initial_similarity_threshold)

    # Step 2: Recursively split large or diverse chunks
    final_chunks = []
    for chunk_sentences in initial_chunks:
        chunk_embeds = embed_sentences(chunk_sentences, model)
        split_chunks = recursive_split(chunk_sentences, chunk_embeds, model, max_tokens, recursive_similarity_threshold)
        final_chunks.extend(split_chunks)

    return final_chunks