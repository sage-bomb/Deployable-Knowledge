from __future__ import annotations
from typing import List, Dict

def rank_chunks(chunks: List[Dict]) -> List[Dict]:
    """Sort context chunks by descending score if present."""
    return sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
