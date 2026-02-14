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
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
}

SYSTEM_DIRS_POSIX = {
    Path("/"),
    Path("/etc"),
    Path("/usr"),
    Path("/var"),
    Path("/bin"),
    Path("/sbin"),
    Path("/lib"),
    Path("/lib64"),
}

SYSTEM_DIR_NAMES_WINDOWS = {"Windows", "Program Files", "Program Files (x86)"}


@dataclass
class IndexStats:
    scanned: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    removed: int = 0


def validate_chunk_parameters(chunk_size: int, overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and less than chunk_size")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    validate_chunk_parameters(chunk_size, overlap)
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
        start = end - overlap
    return chunks


def is_system_directory(root: Path) -> bool:
    resolved = root.resolve()
    anchor = Path(resolved.anchor).resolve()
    if resolved == anchor:
        return True
    if resolved.drive:
        system_dirs = {anchor / name for name in SYSTEM_DIR_NAMES_WINDOWS}
        if resolved in system_dirs:
            return True
    if resolved.anchor == "/" and resolved in SYSTEM_DIRS_POSIX:
        return True
    return False


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
            else:
                logger.warning("Unsupported file extension: %s", root)
            continue
        if is_system_directory(root):
            logger.warning("Skipping system directory: %s", root)
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
    validate_chunk_parameters(chunk_size, overlap)
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
    records, embeddings = store.load_all()
    if embeddings.size == 0:
        return []
    query_vector = model.encode([query])[0]
    # Embeddings are L2-normalized in EmbeddingModel.encode, so dot product == cosine similarity.
    scores = embeddings @ query_vector
    if top_k <= 0:
        return []
    top_k = min(top_k, scores.shape[0])
    if top_k == scores.shape[0]:
        top_indices = np.argsort(scores)[::-1]
    else:
        candidate_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = candidate_indices[np.argsort(scores[candidate_indices])[::-1]]
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
