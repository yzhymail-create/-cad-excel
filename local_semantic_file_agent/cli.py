from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .core import IndexStats, index_paths, search_query
from .embedding import EmbeddingModel
from .storage import LocalVectorStore


DEFAULT_DB_PATH = Path.home() / ".local_semantic_file_agent" / "index.sqlite"
DEFAULT_MODEL = "models/all-MiniLM-L6-v2"


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s:%(name)s:%(message)s",
    )


def _print_index_stats(stats: IndexStats) -> None:
    print("Indexing complete.")
    print(f"Scanned: {stats.scanned}")
    print(f"Indexed: {stats.indexed}")
    print(f"Skipped: {stats.skipped}")
    print(f"Failed: {stats.failed}")
    if stats.removed:
        print(f"Removed missing files: {stats.removed}")


def _print_results(results: list[dict[str, str | float]], snippet_length: int) -> None:
    if not results:
        print("No results found.")
        return
    for idx, result in enumerate(results, start=1):
        content = str(result["content"])
        snippet = content[:snippet_length]
        print(f"{idx}. Score: {result['score']:.4f}")
        print(f"   Path: {result['file_path']}")
        print(f"   Snippet: {snippet}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local Semantic File Agent (offline semantic search)."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index files from directories.")
    index_parser.add_argument(
        "--root",
        "-r",
        action="append",
        required=True,
        help="Root directory or file to index (repeatable).",
    )
    index_parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite database path (default: {DEFAULT_DB_PATH}).",
    )
    index_parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Local embedding model path or cached model name.",
    )
    index_parser.add_argument("--chunk-size", type=int, default=1000)
    index_parser.add_argument("--chunk-overlap", type=int, default=100)
    index_parser.add_argument(
        "--cleanup-missing",
        action="store_true",
        help="Remove records for files missing from scanned roots.",
    )

    search_parser = subparsers.add_parser("search", help="Search indexed files.")
    search_parser.add_argument("--query", "-q", required=True)
    search_parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite database path (default: {DEFAULT_DB_PATH}).",
    )
    search_parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Local embedding model path or cached model name.",
    )
    search_parser.add_argument("--top-k", type=int, default=5)
    search_parser.add_argument("--snippet-length", type=int, default=200)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _configure_logging(args.log_level)

    store = LocalVectorStore(Path(args.db))
    model = EmbeddingModel(args.model)

    try:
        if args.command == "index":
            roots = [Path(root) for root in args.root]
            try:
                stats = index_paths(
                    roots,
                    store,
                    model,
                    args.chunk_size,
                    args.chunk_overlap,
                    args.cleanup_missing,
                )
            except ValueError as exc:
                print(f"Error: {exc}")
                return
            _print_index_stats(stats)
        elif args.command == "search":
            results = search_query(args.query, store, model, args.top_k)
            _print_results(results, args.snippet_length)
    finally:
        store.close()
