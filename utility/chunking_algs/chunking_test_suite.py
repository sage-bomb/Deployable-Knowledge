from typing import List, Callable, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
import sys
from contextlib import contextmanager
import re

class ChunkingTestSuite:
    def __init__(
        self,
        texts: List[str],
        chunking_methods: List[Tuple[str, Callable[[str], List[str]]]],  # (name, func)
        queries_with_answers: List[Tuple[str, str]],  # (query, ideal_answer)
        embedding_models: List[str]
    ):
        self.texts = texts
        self.chunking_methods = chunking_methods
        self.queries_with_answers = queries_with_answers
        self.models = embedding_models

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)

    def semantic_search(self, query_embedding: np.ndarray, chunk_embeddings: np.ndarray) -> int:
        # returns index of best matching chunk
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        return np.argmax(similarities)

    def evaluate_chunking_models_thresholds(self, chunking_methods: list, models: list, thresholds: list) -> dict:
        results = {}

        for chunk_method_name, chunk_fn_template in chunking_methods:
            print(f"\n=== Evaluating chunking method: {chunk_method_name} ===")

            for model in models:
                print(f"\n--- Using embedding model: {model} ---")
                self.model = SentenceTransformer(model)  # set current model

                for threshold in thresholds:
                    print(f"\n>> Threshold = {threshold}")

                    # Inject threshold into chunking function
                    def chunk_fn(text):
                        return chunk_fn_template(text, similarity_threshold=threshold)

                    all_chunks = []
                    for text in self.texts:
                        chunks = chunk_fn(text)
                        all_chunks.extend(chunks)

                    chunk_embeddings = self.embed_texts(all_chunks)
                    best_scores = []

                    for query_idx, (query, ideal_answer) in enumerate(self.queries_with_answers):
                        query_embedding = self.embed_texts([query])[0]
                        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
                        best_idx = similarities.argmax()
                        best_chunk = all_chunks[best_idx]

                        fuzzy_score = fuzz.partial_ratio(ideal_answer.lower(), best_chunk.lower())
                        best_scores.append(fuzzy_score / 100)

                        print(f"\nQuery #{query_idx + 1}")
                        print(f"Fuzzy score: {fuzzy_score}")
                        print(f"Best chunk:\n{best_chunk}")
                        print("-" * 80)

                    avg_score = sum(best_scores) / len(best_scores) if best_scores else 0
                    key = (chunk_method_name, model, threshold)
                    results[key] = avg_score

        return results
    
class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, message):
        for s in self.streams:
            s.write(message)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

@contextmanager
def log_to_file_and_console(log_path):
    original_stdout = sys.stdout
    with open(log_path, "w", encoding="utf-8") as log_file:
        sys.stdout = Tee(sys.stdout, log_file)
        try:
            yield
        finally:
            sys.stdout = original_stdout

if __name__ == "__main__":

    def simple_split(text):
        return [p.strip() for p in text.split('\n\n') if p.strip()]
    
    def safe_sent_tokenize(text):
        return re.split(r'(?<=[.!?]) +', text.strip())

    def sentence_chunk(text):
        return safe_sent_tokenize(text)

    queries_with_answers = [
        ("What does clicking the Summary button do", "Clicking the Summary button hides the details about the connection, restricting the information to the IP address, Type, Slot, Status, and Description."),
        ("What does the Cisco Easy VPN Remote feature implement", "The Cisco Easy VPN Remote feature implements the Cisco Unity Client protocol, which allows most VPN parameters to be defined at a VPN remote access server."),
        ("What kind of certificates can be revoked", "Only issued certificates can be revoked"),
        ("What do the Authentication Policies and the Authorization Policies windows do", "The Authentication Policies and the Authorization Policies windows summarize the authentication policy information on the router.")
    ]

    chunking_methods = [
        
    ]

    thresholds_to_test = [0.5, 0.6, 0.7, 0.8, 0.9]

    transformer_models = ["all-mpnet-base-v2", "multi-qa-mpnet-base-dot-v1", "all-MiniLM-L12-v2"]

    log_file_path = "chunking_test_log.txt"
    with log_to_file_and_console(log_file_path):
        suite = ChunkingTestSuite(texts, chunking_methods, queries_with_answers, transformer_models)
        results = suite.evaluate_chunking_models_thresholds(
            chunking_methods,
            transformer_models,
            thresholds_to_test
        )

        print("\nFinal results by threshold:")
        for t, score in results.items():
            print(f"Threshold {t}: Avg fuzzy score = {score:.3f}")

    print(f"\nAll output was also saved to: {log_file_path}")
