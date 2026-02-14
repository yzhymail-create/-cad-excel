from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from .embedding import EmbeddingModel
from .extractors import extract_text
from .storage import LocalVectorStore


logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".txt",
    ".md",
    ".pptx",
    ".ppt",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
}


@dataclass
class IndexStats:
    scanned: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    removed: int = 0


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def iter_candidate_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        root = root.expanduser()
        if not root.exists():
            logger.warning("Path does not exist: %s", root)
            continue
        if root.is_symlink():
            logger.warning("Skipping symlink root: %s", root)
            continue
        if root.is_file():
            if root.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield root
            continue
        if root == Path(root.anchor):
            logger.warning("Skipping system root directory: %s", root)
            continue
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    yield path


def index_paths(
    roots: Iterable[Path],
    store: LocalVectorStore,
    model: EmbeddingModel,
    chunk_size: int,
    overlap: int,
    cleanup_missing: bool,
) -> IndexStats:
    stats = IndexStats()
    scanned_files: set[str] = set()

    for path in iter_candidate_files(roots):
        stats.scanned += 1
        file_path = str(path)
        scanned_files.add(file_path)
        try:
            metadata = store.get_file_metadata(file_path)
            stat = path.stat()
            current_meta = (stat.st_mtime, stat.st_size)
            if metadata == current_meta:
                stats.skipped += 1
                continue
            text = extract_text(path)
            chunks = chunk_text(text, chunk_size, overlap)
            if not chunks:
                stats.skipped += 1
                continue
            embeddings = model.encode(chunks)
            store.replace_file(file_path, stat.st_mtime, stat.st_size, chunks, embeddings)
            stats.indexed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to index %s: %s", path, exc)
            stats.failed += 1

    if cleanup_missing:
        missing = store.list_files() - scanned_files
        if missing:
            store.remove_files(missing)
            stats.removed = len(missing)

    return stats


def search_query(
    query: str,
    store: LocalVectorStore,
    model: EmbeddingModel,
    top_k: int,
) -> list[dict[str, str | float]]:
    records, embeddings = store.load_embeddings()
    if embeddings.size == 0:
        return []
    query_vector = model.encode([query])[0]
    scores = embeddings @ query_vector
    top_indices = np.argsort(scores)[::-1][:top_k]
    results: list[dict[str, str | float]] = []
    for index in top_indices:
        file_path, content = records[int(index)]
        results.append(
            {
                "file_path": file_path,
                "score": float(scores[int(index)]),
                "content": content,
            }
        )
    return results
