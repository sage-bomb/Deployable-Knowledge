# This chunking method starts with each of the sentences (or paragraphs) and continually merges if a certain similarity threshold is met

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import re

nltk.download('punkt')
from nltk.tokenize import sent_tokenize

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed(text):
    return model.encode([text])[0]

# NLTK hates human life and demands you all suffer at the hands of bad pickles.. all for the sake of a sentance spliter.
def safe_sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text.strip())

def merge_sentences_bottom_up(text, similarity_threshold):
    sentences = safe_sent_tokenize(text)
    chunks = sentences[:]  # start each sentence as a chunk
    
    embeddings = [embed(s) for s in chunks]

    merged = True
    while merged and len(chunks) > 1:
        merged = False
        new_chunks = []
        new_embeddings = []
        i = 0
        while i < len(chunks):
            if i < len(chunks) - 1:
                sim = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
                if sim > similarity_threshold:
                    # merge adjacent chunks
                    merged_chunk = chunks[i] + " " + chunks[i+1]
                    merged_embedding = embed(merged_chunk)
                    new_chunks.append(merged_chunk)
                    new_embeddings.append(merged_embedding)
                    i += 2
                    merged = True
                    continue
            new_chunks.append(chunks[i])
            new_embeddings.append(embeddings[i])
            i += 1
        chunks, embeddings = new_chunks, new_embeddings
    return chunks