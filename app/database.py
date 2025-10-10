"""Supabase client initialisation with an in-memory fallback for tests."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, List

from supabase import Client, create_client

from .config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class _InsertResult:
    data: List[Dict[str, Any]]
    error: Any = None


class _InsertBuilder:
    def __init__(self, table: "_InMemoryTable", record: Dict[str, Any]):
        self._table = table
        self._record = record

    def execute(self) -> _InsertResult:
        return self._table._insert(self._record)


class _InMemoryTable:
    def __init__(self, name: str):
        self._name = name
        self._records: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._next_id = 1

    def insert(self, record: Dict[str, Any]) -> _InsertBuilder:
        return _InsertBuilder(self, record)

    def _insert(self, record: Dict[str, Any]) -> _InsertResult:
        with self._lock:
            stored = {"id": self._next_id, **record}
            self._records.append(stored)
            self._next_id += 1
        return _InsertResult(data=[stored])

    # Convenience for tests
    @property
    def records(self) -> List[Dict[str, Any]]:
        return list(self._records)


class InMemorySupabaseClient:
    """Very small in-memory stand-in that mimics Supabase's ``table`` API."""

    def __init__(self):
        self._tables: Dict[str, _InMemoryTable] = {}
        self._lock = threading.Lock()

    def table(self, name: str) -> _InMemoryTable:
        with self._lock:
            if name not in self._tables:
                self._tables[name] = _InMemoryTable(name)
            return self._tables[name]


def _create_supabase_client() -> Client | InMemorySupabaseClient:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_key:
        try:
            return create_client(settings.supabase_url, settings.supabase_key)
        except Exception as exc:  # pragma: no cover - only triggered when Supabase misconfigured.
            logger.warning("Failed to create Supabase client, using in-memory store: %s", exc)
    else:
        logger.info("Supabase credentials not provided; using in-memory store")
    return InMemorySupabaseClient()


supabase: Client | InMemorySupabaseClient = _create_supabase_client()

__all__ = ["supabase", "InMemorySupabaseClient"]
