"""Python AST correspondence experiment for complete function hunks."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from reviewability.domain.models import Hunk

_MIN_IDENTIFIER_OVERLAP = 0.4


@dataclass(frozen=True)
class PythonFunctionMatch:
    """A high-confidence correspondence between two complete Python functions."""

    source: Hunk
    target: Hunk
    identifier_overlap: float


def match_python_functions(hunks: list[Hunk]) -> list[PythonFunctionMatch]:
    """Match complete removed/added Python functions using AST identifiers.

    This intentionally returns no result for partial functions, classes, or invalid
    snippets. It is an experiment for evaluating structural evidence, not a fallback
    for the generic hunk matcher.
    """
    source_functions = [
        (hunk, function)
        for hunk in hunks
        if (function := _parse_single_function(hunk.raw_removed_lines)) is not None
    ]
    target_functions = [
        (hunk, function)
        for hunk in hunks
        if (function := _parse_single_function(hunk.raw_added_lines)) is not None
    ]
    candidates = [
        (
            _identifier_overlap(source_function, target_function),
            source_hunk,
            target_hunk,
        )
        for source_hunk, source_function in source_functions
        for target_hunk, target_function in target_functions
        if source_hunk is not target_hunk
    ]
    candidates.sort(reverse=True, key=lambda candidate: candidate[0])

    matched_hunks: set[int] = set()
    matches = []
    for overlap, source, target in candidates:
        if overlap < _MIN_IDENTIFIER_OVERLAP:
            continue
        if id(source) in matched_hunks or id(target) in matched_hunks:
            continue
        matches.append(PythonFunctionMatch(source, target, overlap))
        matched_hunks.update((id(source), id(target)))
    return matches


def _parse_single_function(lines: list[str]) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    try:
        module = ast.parse("".join(lines))
    except SyntaxError:
        return None
    if len(module.body) != 1:
        return None
    node = module.body[0]
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    return node


def _identifier_overlap(
    source: ast.FunctionDef | ast.AsyncFunctionDef,
    target: ast.FunctionDef | ast.AsyncFunctionDef,
) -> float:
    source_identifiers = _identifiers(source)
    target_identifiers = _identifiers(target)
    union = source_identifiers | target_identifiers
    return len(source_identifiers & target_identifiers) / len(union) if union else 0.0


def _identifiers(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    identifiers = {function.name}
    identifiers.update(argument.arg for argument in function.args.args)
    identifiers.update(node.id for node in ast.walk(function) if isinstance(node, ast.Name))
    identifiers.update(node.attr for node in ast.walk(function) if isinstance(node, ast.Attribute))
    return identifiers
