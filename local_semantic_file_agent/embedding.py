from __future__ import annotations

import os
from typing import Iterable

import numpy as np


class EmbeddingModel:
    def __init__(self, model_name: str) -> None:
        self.dimension = 0
        self._model_name = model_name.lower()
        self._use_hashing = self._model_name == "hashing"
        if self._use_hashing:
            self._init_hashing()
            return

        self._configure_offline_mode()
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required. Install dependencies from requirements.txt."
            ) from exc

        try:
            self._model = SentenceTransformer(model_name, device="cpu")
        except OSError as exc:
            raise RuntimeError(
                "Embedding model not found locally. "
                "Download the model to a local path and pass --model."
            ) from exc

        self.dimension = self._model.get_sentence_embedding_dimension()

    @staticmethod
    def _configure_offline_mode() -> None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        text_list = list(texts)
        if self._use_hashing:
            embeddings = self._vectorizer.transform(text_list).toarray()
            return np.asarray(embeddings, dtype=np.float32)
        embeddings = self._model.encode(
            text_list,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def _init_hashing(self) -> None:
        try:
            from sklearn.feature_extraction.text import HashingVectorizer
        except ImportError as exc:
            raise RuntimeError(
                "scikit-learn is required for hashing embeddings."
            ) from exc
        self._vectorizer = HashingVectorizer(
            n_features=768,
            alternate_sign=False,
            norm="l2",
            analyzer="char",
            ngram_range=(2, 4),
        )
        self.dimension = 768
