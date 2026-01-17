"""Helpers to compile Blink schema text into runtime Schema objects."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .parser import parse_schema
from .resolve import resolve_schema
from .model import Schema


def compile_schema(text: str, *, filename: str | None = None) -> Schema:
    """
    Parse and resolve Blink schema text in a single call.

    Args:
        text: Raw Blink schema document.
        filename: Optional identifier used for error reporting.
    Returns:
        A fully resolved ``Schema`` instance ready for registry or codec use.
    """

    schema_ast = parse_schema(text, filename=filename)
    return resolve_schema(schema_ast)


def compile_schema_file(path: str | Path) -> Schema:
    """Read, parse, and resolve a Blink schema from ``path``."""

    resolved_path = Path(path)
    text = resolved_path.read_text(encoding="utf-8")
    return compile_schema(text, filename=str(resolved_path))


__all__ = ["compile_schema", "compile_schema_file"]
