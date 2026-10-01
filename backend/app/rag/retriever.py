"""Policy RAG retriever module."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

from .. import config


def _split_into_sections(markdown_text: str) -> List[str]:
    parts = re.split(r"\n(?=## )", markdown_text.strip())
    return [p.strip() for p in parts if p.strip()]


@dataclass
class ScoredChunk:
    text: str
    score: float


class PolicyRetriever:
    """Retrieves relevant company policy chunks using embeddings with keyword fallback."""

    def __init__(self, markdown_path=config.POLICY_PATH):
        self.chunks: List[str] = []
        self._unit_matrix: Optional[np.ndarray] = None
        self._embeddings = None

        try:
            text = markdown_path.read_text(encoding="utf-8")
        except Exception:
            text = (
                "## Baggage Policy\nPassengers are allowed 1 carry-on and 1 personal item. "
                "Checked bags cost $35 for the first bag.\n\n"
                "## Ticket Changes\nChanges allowed up to 3 hours prior to departure. "
                "Change fees apply for Economy tickets.\n\n"
                "## Cancellations\nFull refund within 24 hours of booking, credit thereafter.\n\n"
                "## Hotels & Cars\nBookings can be modified or cancelled according to partner terms."
            )

        self.chunks = _split_into_sections(text)

        if config.GOOGLE_API_KEY:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    model=config.GOOGLE_EMBEDDING_MODEL,
                    google_api_key=config.GOOGLE_API_KEY,
                )
                vectors = self._embeddings.embed_documents(self.chunks)
                matrix = np.array(vectors, dtype=np.float32)
                norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                norms[norms == 0] = 1e-9
                self._unit_matrix = matrix / norms
            except Exception as e:
                self._embeddings = None

    def _keyword_search(self, query: str, k: int = 2) -> List[ScoredChunk]:
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for chunk in self.chunks:
            chunk_words = set(re.findall(r"\w+", chunk.lower()))
            overlap = len(query_words & chunk_words)
            score = overlap / max(len(query_words), 1)
            scored.append(ScoredChunk(text=chunk, score=score))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    def query(self, text: str, k: int = 2) -> List[ScoredChunk]:
        if self._embeddings and self._unit_matrix is not None:
            try:
                vec = np.array(self._embeddings.embed_query(text), dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                scores = self._unit_matrix @ vec
                top_idx = np.argsort(-scores)[:k]
                return [ScoredChunk(text=self.chunks[i], score=float(scores[i])) for i in top_idx]
            except Exception:
                pass

        return self._keyword_search(text, k=k)


_singleton: Optional[PolicyRetriever] = None


def get_retriever() -> PolicyRetriever:
    global _singleton
    if _singleton is None:
        _singleton = PolicyRetriever()
    return _singleton
