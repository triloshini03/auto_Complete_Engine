"""JSON-backed search history with a small, thread-safe API."""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


class SearchHistory:
    """Persist recent searches and expose counts for ranking."""

    def __init__(self, path, max_entries=500):
        self.path = Path(path)
        self.max_entries = max_entries
        self._lock = threading.Lock()

    def _read_entries(self):
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as history_file:
            entries = json.load(history_file)
        if not isinstance(entries, list):
            raise ValueError("search history must contain a JSON list")
        return [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("query"), str)
            and isinstance(entry.get("searched_at"), str)
        ]

    def _write_entries(self, entries):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_name(self.path.name + ".tmp")
        try:
            with temporary_path.open("w", encoding="utf-8") as history_file:
                json.dump(entries, history_file, ensure_ascii=False, indent=2)
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def record(self, query):
        """Add a search to history and return its stored entry."""
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        normalized = query.strip()
        if not normalized:
            raise ValueError("query cannot be empty")

        entry = {
            "query": normalized,
            "searched_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            entries = self._read_entries()
            self._write_entries(([entry] + entries)[: self.max_entries])
        return entry

    def recent(self, limit=8):
        """Return unique recent queries, newest first."""
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")
        with self._lock:
            entries = self._read_entries()

        recent_entries = []
        seen = set()
        for entry in entries:
            normalized = entry["query"].casefold()
            if normalized not in seen:
                seen.add(normalized)
                recent_entries.append(entry)
                if len(recent_entries) >= limit:
                    break
        return recent_entries

    def counts(self):
        """Return case-insensitive query counts for ranking."""
        with self._lock:
            entries = self._read_entries()
        counts = {}
        for entry in entries:
            query = entry["query"].strip().casefold()
            if query:
                counts[query] = counts.get(query, 0) + 1
        return counts

    def clear(self):
        """Remove all stored searches."""
        with self._lock:
            self._write_entries([])
