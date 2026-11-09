
"""
SONORA AI Phase 2 - Semantic Embedding Engine

Features:
- Sentence Transformer embeddings
- Semantic text similarity
- Vector-based similar-track retrieval
- Cosine similarity scoring
- Safe TF-IDF fallback when embeddings are unavailable

Enable embeddings using:
    SONORA_EMBEDDINGS=1

Optional model:
    SONORA_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
"""

from __future__ import annotations


import os
from typing import Optional

import numpy as np
from dotenv import load_dotenv

# Load environment variables before initializing the engine
load_dotenv()


class SemanticEmbeddingIndex:

    def __init__(self, documents: list[str]):

        self.documents = documents

        self.enabled = (
            os.getenv("SONORA_EMBEDDINGS", "0")
            .strip()
            .lower()
            in {"1", "true", "yes", "on"}
        )

        self.model_name = os.getenv(
            "SONORA_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )

        self.model = None
        self.document_vectors = None

        self.error = None
        self._attempted = False

    def _load(self) -> bool:
        """
        Load the embedding model and encode catalogue documents.

        The model is loaded only when embedding mode is enabled.
        """

        if not self.enabled:
            return False

        if self._attempted:
            return self.model is not None

        self._attempted = True

        try:

            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)

            vectors = self.model.encode(
                self.documents,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            self.document_vectors = np.asarray(
                vectors,
                dtype=np.float32,
            )

            return True

        except Exception as exc:

            self.error = f"{type(exc).__name__}: {exc}"

            self.model = None
            self.document_vectors = None

            return False

    def query_scores(
        self,
        query: str,
    ) -> Optional[np.ndarray]:
        """
        Calculate semantic similarity between a query and all tracks.

        Returns scores between 0 and 1.
        Returns None when embeddings are unavailable.
        """

        if not self._load():
            return None

        try:

            query_vector = self.model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )[0]

            cosine = (
                self.document_vectors
                @ np.asarray(
                    query_vector,
                    dtype=np.float32,
                )
            )

            scores = np.clip(
                (cosine + 1.0) / 2.0,
                0.0,
                1.0,
            )

            return scores

        except Exception as exc:

            self.error = f"{type(exc).__name__}: {exc}"

            return None

    def similar_indices(
        self,
        index: int,
        limit: int = 10,
    ) -> Optional[list[tuple[int, float]]]:
        """
        Find tracks most similar to a selected catalogue track.

        Returns:
            [(track_index, similarity_score), ...]

        Returns None when embeddings are unavailable.
        """

        if not self._load():
            return None

        if index < 0 or index >= len(self.documents):
            return []

        scores = (
            self.document_vectors
            @ self.document_vectors[index]
        )

        order = np.argsort(-scores)

        results = []

        for i in order:

            if int(i) == index:
                continue

            similarity = float(
                (scores[i] + 1.0) / 2.0
            )

            results.append(
                (int(i), similarity)
            )

            if len(results) >= limit:
                break

        return results

    def status(self) -> dict:
        """
        Return the current semantic engine status.
        """

        loaded = self.model is not None

        return {
            "embedding_requested": self.enabled,

            "embedding_loaded": loaded,

            "model": (
                self.model_name
                if loaded
                else None
            ),

            "vector_count": (
                int(len(self.documents))
                if loaded
                else 0
            ),

            "dimension": (
                int(self.document_vectors.shape[1])
                if loaded
                and self.document_vectors is not None
                else None
            ),

            "fallback": "tfidf",

            "error": self.error,
        }
