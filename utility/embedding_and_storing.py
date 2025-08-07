from pathlib import Path
from typing import List, Tuple, Dict, Optional
import re

from utility.db_manager import DBManager
from utility.parsing import parse_pdf
from utility.chunking_algs.chunker import (
    chunk_by_sentences,
    chunk_by_semantic_similarity,
    safe_chunk_by_graph_rank,
    chunk_by_paragraphs,
)
from utility.chunking_algs.dynamic_bottom_to_top_chunking import merge_sentences_bottom_up
from utility.chunking_algs.graph_pagerank_chunking import pagerank_chunk_text
from utility.model_utils import load_embedding_model

# === Config ===
from config import (
    CHROMA_DB_DIR,
    COLLECTION_NAME,
    DEFAULT_CHUNKING_METHOD,
    CHUNKING_METHOD_OPTIONS,
)

# === DB Setup ===
embedding_model = load_embedding_model()
db = DBManager(persist_dir=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, model=embedding_model)

def chunk_text(text: str, method: str = "graph") -> List[Tuple[str, Dict]]:
    """
    Chunk text based on the specified method.

    Args:
        text (str): The input text to be chunked.
        method (str): The chunking method to use. Options include:
            - "sentences": Split by sentences.
            - "semantics": Split by semantic similarity.
            - "graph": Use graph-based ranking for chunking.
            - "paragraphs": Split by paragraphs.
            - "dynamic": Merge sentences dynamically based on similarity.
            - "graph-pagerank": Use PageRank algorithm for chunking.

    Returns:
        List[Tuple[str, Dict]]: A list of tuples where each tuple contains the chunked text and its metadata.
    """
    if method == "sentences":
        return chunk_by_sentences(text, max_chars=500)
    elif method == "semantics":
        return chunk_by_semantic_similarity(text, model=embedding_model, threshold=0.6)
    elif method == "graph":
        return safe_chunk_by_graph_rank(text, max_sentences=4, model=embedding_model)
    elif method == "paragraphs":
        return chunk_by_paragraphs(text, model=embedding_model, threshold=0.7)
    elif method == "dynamic":
        return merge_sentences_bottom_up(text, similarity_threshold=0.7, model=embedding_model)
    elif method == "graph-pagerank":
        return pagerank_chunk_text(text, model=embedding_model, sim_threshold=0.7)
    else:
        raise ValueError(f"Unsupported chunking method: {method}")
    
def is_all_caps(text, threshold=0.8):
    """
    Check if a text is predominantly uppercase, ignoring non-alphabetic characters.

    Args:
        text (str): The input text to check.
        threshold (float): The proportion of uppercase characters to consider as "all caps".
        
    Returns:
        bool: True if the text is predominantly uppercase, False otherwise.
    """
    cleaned = re.sub(r'[\W\d_]+', '', text)
    if not cleaned:
        return False
    upper_count = sum(1 for c in cleaned if c.isupper())
    return (upper_count / len(cleaned)) >= threshold

def extract_text(file_path: Path) -> str:
    """
    Extract text from a file based on its type.

    Args:
        file_path (Path): Path to the file to extract text from.

    Returns:
        List[Dict]: List of dictionaries with page number and text content.
    """
    if file_path.suffix.lower() == ".pdf":
        return parse_pdf(str(file_path))
    elif file_path.suffix.lower() == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return [{"page 1": 1, "text": text}]
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

def embed_file(
    file_path: Path,
    chunking_method: str = "graph",
    source_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    filter_chunks: bool = True,
) -> None:
    """
    Process a single file: parse, chunk, embed, store.

    Args:
        file_path (Path): Path to the file to be processed.
        chunking_method (str): Method to use for chunking the text.
        source_name (Optional[str]): Optional name for the source of the file.
        tags (Optional[List[str]]): Optional tags to associate with the segments.
        filter_chunks (bool): Whether to filter out all-uppercase chunks and repeated substrings.
    
    Returns:
        None: The function stores the segments in the database.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"📄 Embedding file: {file_path.name}")
    
    pages = extract_text(file_path)  # expects list of dicts {"page": n, "text": "..."}
    
    all_chunks_with_meta = []

    for page in pages:
        page_num = page.get("page")
        page_text = page.get("text", "")
        print(f"Page {page_num} length: {len(page_text)}")
        
        # Chunk page text separately
        chunks_with_meta = chunk_text(page_text, method=chunking_method)
        
        # Add page info directly to meta for each chunk
        for chunk_text_, meta in chunks_with_meta:
            meta["page"] = page_num
            all_chunks_with_meta.append((chunk_text_, meta))
    # Optional filtering on all chunks
    if filter_chunks:
        all_chunks_with_meta = [
            (chunk, meta) for chunk, meta in all_chunks_with_meta if not is_all_caps(chunk)
        ]
        def has_repeated_substring(text, patterns=None):
            chars = re.sub(r'\s+', '', text)
            if patterns is None:
                patterns = [r'\.{3,}', r'-{3,}', r'_{3,}']
            return any(re.search(p, chars) for p in patterns)

        all_chunks_with_meta = [
            (chunk, meta) for chunk, meta in all_chunks_with_meta if not has_repeated_substring(chunk)
        ]
    
    all_chunks_with_meta = [
        (chunk, meta) for chunk, meta in all_chunks_with_meta if len(chunk.split()) >= 5
    ]

    segments = [chunk for chunk, _ in all_chunks_with_meta]
    positions = [meta.get("char_range", (None, None)) for _, meta in all_chunks_with_meta]
    pages = [meta.get("page") for _, meta in all_chunks_with_meta]

    db.add_segments(
        segments=segments,
        strategy_name=chunking_method,
        source=source_name or file_path.name,
        tags=tags or ["embedded"],
        positions=positions,
        page=pages,
    )

    print(f"✅ File embedded: {file_path.name}")


def embed_directory(
    data_dir: str,
    chunking_method: str = "graph",
    clear_collection: bool = False,
    default_tags: Optional[List[str]] = None,
    filter_chunks: bool = False,
):
    """
    Embed all supported files in a directory using the specified chunking method.

    Args:
        data_dir (str): Directory containing text files to embed.
        chunking_method (str): Method to use for chunking the text.
        clear_collection (bool): Whether to clear the collection before inserting new data.
        default_tags (Optional[List[str]]): Default tags to apply to all segments.
        filter_chunks (bool): Whether to filter out all-uppercase chunks and repeated substrings during chunking.
    
    Returns:
        None: The function processes and stores the segments in the database.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    if clear_collection:
        db.clear_collection()

    print(f"🔍 Embedding from: {data_path.resolve()}")
    print(f"📚 Using method: {chunking_method}")
    print(f"🧹 Clearing collection: {'Yes' if clear_collection else 'No'}")

    supported_extensions = [".txt", ".pdf"]
    for file_path in data_path.iterdir():
        if file_path.suffix.lower() not in supported_extensions:
            print(f"⚠️ Skipping unsupported file type: {file_path.name}")
            continue

        try:
            embed_file(
                file_path=file_path,
                chunking_method=chunking_method,
                source_name=file_path.name,
                tags=default_tags or ["embedded"],
                filter_chunks=filter_chunks
            )
        except Exception as e:
            print(f"❌ Failed to embed {file_path.name}: {e}")

    print("\n✅ All supported documents embedded and stored.")


# === CLI Entry ===
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embed and store text documents with configurable chunking.")
    parser.add_argument("--data_dir", type=str, default="documents", help="Directory with .txt files")
    parser.add_argument("--chunking_method", type=str, default="graph", choices=CHUNKING_METHOD_OPTIONS)
    parser.add_argument("--clear_collection", action="store_true", help="Clear collection before inserting")
    parser.add_argument("--filter_chunks", action="store_true", help="Filter out all-uppercase chunks (usually headers) during chunking")
    args = parser.parse_args()

    embed_directory(
        data_dir=args.data_dir,
        chunking_method=args.chunking_method,
        clear_collection=args.clear_collection,
        default_tags=["testing"],
        filter_chunks=args.filter_chunks
    )