from typing import List, Callable, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

# We have different testing suites, in which we use the recall, recall@k and fuzzy matching metrics to test different chunking models to determine which 
# models output the best results. The fuzzy matching metric seems to work well to determine whether a response contains a "close enough" answer to the question.

class ChunkingTestSuite:
    def __init__(
        self,
        texts: List[str],
        chunking_methods: List[Tuple[str, Callable[[str], List[str]]]],  # (name, func)
        queries_with_answers: List[Tuple[str, str]],  # (query, ideal_answer)
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        self.texts = texts
        self.chunking_methods = chunking_methods
        self.queries_with_answers = queries_with_answers
        self.model = SentenceTransformer(embedding_model_name)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)

    def semantic_search(self, query_embedding: np.ndarray, chunk_embeddings: np.ndarray) -> int:
        # returns index of best matching chunk
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        return np.argmax(similarities)

    def evaluate_recall_at_k(self, k=3) -> dict:
        results = {}

        for method_name, chunk_fn in self.chunking_methods:
            recalls = []
            print(f"\n=== Evaluating chunking method: {method_name} ===")

            # Step 1: Chunk all documents and combine
            all_chunks = []
            for doc_idx, text in enumerate(self.texts):
                chunks = chunk_fn(text)
                all_chunks.extend(chunks)

            # Step 2: Embed all combined chunks once
            all_embeddings = self.embed_texts(all_chunks)

            # Step 3: For each query, run semantic search on combined embeddings
            for query_idx, (query, ideal_answer) in enumerate(self.queries_with_answers):
                query_emb = self.embed_texts([query])[0]
                similarities = cosine_similarity([query_emb], all_embeddings)[0]

                # Get indices of top-k chunks (descending order)
                top_k_idx = similarities.argsort()[-k:][::-1]

                # Check if ideal answer is found in any top-k chunk (case-insensitive)
                found = any(
                    ideal_answer.lower() in all_chunks[idx].lower() for idx in top_k_idx
                )
                recalls.append(int(found))

                # Print results for this query
                print(f"\nQuery #{query_idx + 1}: '{query}'")
                print(f"Ideal answer snippet: '{ideal_answer[:80]}{'...' if len(ideal_answer) > 80 else ''}'")
                print(f"Found in top-{k} chunks? {'YES' if found else 'NO'}")
                print("Top chunks retrieved:")
                for rank, idx in enumerate(top_k_idx, 1):
                    snippet = all_chunks[idx].replace("\n", " ")[:100]
                    score = similarities[idx]
                    print(f"  {rank}. (score={score:.3f}) {snippet}{'...' if len(all_chunks[idx]) > 100 else ''}")
                print()

            avg_recall = np.mean(recalls) if recalls else 0
            results[method_name] = avg_recall

        return results

    def evaluate_recall(self) -> dict:
        results = {}

        for method_name, chunk_fn in self.chunking_methods:
            recalls = []
            print(f"\n=== Evaluating chunking method: {method_name} ===")

            # Chunk all documents and combine
            all_chunks = []
            for doc_idx, text in enumerate(self.texts):
                chunks = chunk_fn(text)
                all_chunks.extend(chunks)

            # Embed all chunks once
            all_embeddings = self.embed_texts(all_chunks)

            # For each query, embed and compute similarities
            for query_idx, (query, ideal_answer) in enumerate(self.queries_with_answers):
                query_emb = self.embed_texts([query])[0]
                similarities = cosine_similarity([query_emb], all_embeddings)[0]

                # Check if ideal answer appears in any chunk (case insensitive)
                found = any(
                    ideal_answer.lower() in chunk.lower() for chunk in all_chunks
                )
                recalls.append(int(found))

                # Print query results
                print(f"\nQuery #{query_idx + 1}: '{query}'")
                print(f"Ideal answer snippet: '{ideal_answer[:80]}{'...' if len(ideal_answer) > 80 else ''}'")
                print(f"Found anywhere in chunks? {'YES' if found else 'NO'}")

            avg_recall = np.mean(recalls) if recalls else 0
            results[method_name] = avg_recall

        return results
    
    def evaluate_fuzzy_best_match(self) -> dict:
        results = {}

        for method_name, chunk_fn in self.chunking_methods:
            best_scores = []
            print(f"\n=== Evaluating chunking method: {method_name} (best fuzzy match per query) ===")

            # Chunk all documents and combine
            all_chunks = []
            for doc_idx, text in enumerate(self.texts):
                chunks = chunk_fn(text)
                all_chunks.extend(chunks)

            # For each query, compute fuzzy similarity with all chunks
            for query_idx, (query, ideal_answer) in enumerate(self.queries_with_answers):
                ideal_answer_lower = ideal_answer.lower()
                scores = [fuzz.partial_ratio(ideal_answer_lower, chunk.lower()) for chunk in all_chunks]

                # Find best score and index
                best_score = max(scores) if scores else 0
                best_idx = scores.index(best_score) if scores else -1
                best_scores.append(best_score / 100)  # Normalize to 0-1 range

                # Print query and best match info
                print(f"\nQuery #{query_idx + 1}: '{query}'")
                print(f"Ideal answer snippet: '{ideal_answer[:80]}{'...' if len(ideal_answer) > 80 else ''}'")
                if best_idx >= 0:
                    snippet = all_chunks[best_idx].replace("\n", " ")[:150]
                    print(f"Best fuzzy match score: {best_score} (chunk snippet: {snippet}{'...' if len(all_chunks[best_idx]) > 150 else ''})")
                else:
                    print("No chunks found.")

            avg_best_score = sum(best_scores) / len(best_scores) if best_scores else 0
            results[method_name] = avg_best_score

        return results