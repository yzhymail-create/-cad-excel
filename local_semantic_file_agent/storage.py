from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable

import numpy as np


logger = logging.getLogger(__name__)


class LocalVectorStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.db_path))
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS files (
                file_path TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                size INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                embedding_dim INTEGER NOT NULL,
                FOREIGN KEY(file_path) REFERENCES files(file_path)
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(file_path);
            """
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def get_file_metadata(self, file_path: str) -> tuple[float, int] | None:
        cursor = self._connection.execute(
            "SELECT mtime, size FROM files WHERE file_path = ?", (file_path,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return float(row[0]), int(row[1])

    def list_files(self) -> set[str]:
        cursor = self._connection.execute("SELECT file_path FROM files")
        return {row[0] for row in cursor.fetchall()}

    def replace_file(
        self,
        file_path: str,
        modification_time: float,
        size: int,
        chunks: Iterable[str],
        embeddings: np.ndarray,
    ) -> None:
        with self._connection:
            self._connection.execute(
                "DELETE FROM chunks WHERE file_path = ?", (file_path,)
            )
            self._connection.execute(
                "REPLACE INTO files (file_path, mtime, size) VALUES (?, ?, ?)",
                (file_path, modification_time, size),
            )
            rows = [
                (
                    file_path,
                    index,
                    chunk,
                    embeddings[index].tobytes(),
                    embeddings.shape[1],
                )
                for index, chunk in enumerate(chunks)
            ]
            self._connection.executemany(
                """
                INSERT INTO chunks (file_path, chunk_index, content, embedding, embedding_dim)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )

    def remove_files(self, file_paths: Iterable[str]) -> None:
        with self._connection:
            for file_path in file_paths:
                self._connection.execute(
                    "DELETE FROM chunks WHERE file_path = ?", (file_path,)
                )
                self._connection.execute(
                    "DELETE FROM files WHERE file_path = ?", (file_path,)
                )

    def load_all(self) -> tuple[list[tuple[str, str]], np.ndarray]:
        cursor = self._connection.execute(
            "SELECT file_path, content, embedding, embedding_dim FROM chunks"
        )
        records: list[tuple[str, str]] = []
        vectors: list[np.ndarray] = []
        for file_path, content, embedding_blob, embedding_dim in cursor.fetchall():
            vector = np.frombuffer(embedding_blob, dtype=np.float32)
            if vector.size != embedding_dim:
                logger.warning(
                    "Embedding dimension mismatch for %s (expected %s, got %s)",
                    file_path,
                    embedding_dim,
                    vector.size,
                )
                continue
            records.append((file_path, content))
            vectors.append(vector)
        if not vectors:
            return records, np.empty((0, 0), dtype=np.float32)
        return records, np.vstack(vectors)
