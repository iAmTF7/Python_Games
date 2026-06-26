"""Small persistent high-score table for room-reached runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SCORE_PATH = Path(__file__).resolve().parents[1] / "high_scores.json"


@dataclass(frozen=True)
class HighScoreEntry:
    """One recorded run, ranked by the highest room reached."""

    room_reached: int
    recorded_at: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "HighScoreEntry | None":
        try:
            room_reached = max(1, int(data.get("room_reached", 0)))
        except (TypeError, ValueError):
            return None

        recorded_at = str(data.get("recorded_at") or "unknown")
        return cls(room_reached=room_reached, recorded_at=recorded_at)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "room_reached": self.room_reached,
            "recorded_at": self.recorded_at,
        }


class HighScoreTable:
    """Load, rank, and persist the top room-reached scores."""

    def __init__(self, storage_path: str | Path | None = None, max_entries: int = 5) -> None:
        self.storage_path = Path(storage_path) if storage_path is not None else DEFAULT_SCORE_PATH
        self.max_entries = max(1, int(max_entries))
        self.entries: list[HighScoreEntry] = self._load_entries()

    @property
    def best_room(self) -> int:
        if not self.entries:
            return 1
        return max(entry.room_reached for entry in self.entries)

    def submit(self, room_reached: int) -> HighScoreEntry:
        """Record one run and return the saved entry."""

        entry = HighScoreEntry(
            room_reached=max(1, int(room_reached)),
            recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.entries.append(entry)
        self.entries = self._rank(self.entries)[: self.max_entries]
        self._save_entries()
        return entry

    def display_entries(self, limit: int | None = None) -> list[HighScoreEntry]:
        """Return the current leaderboard entries in display order."""

        count = self.max_entries if limit is None else max(1, int(limit))
        return self.entries[:count]

    def _load_entries(self) -> list[HighScoreEntry]:
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, json.JSONDecodeError):
            return []

        if isinstance(raw, dict):
            raw_entries: Iterable[Any] = raw.get("entries", [])
        elif isinstance(raw, list):
            raw_entries = raw
        else:
            return []

        entries = []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            entry = HighScoreEntry.from_mapping(item)
            if entry is not None:
                entries.append(entry)
        return self._rank(entries)[: self.max_entries]

    def _save_entries(self) -> None:
        payload = {"entries": [entry.to_mapping() for entry in self.entries]}
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
        except OSError:
            # A missing or read-only save location should not crash the game.
            pass

    @staticmethod
    def _rank(entries: Iterable[HighScoreEntry]) -> list[HighScoreEntry]:
        return sorted(entries, key=lambda entry: (-entry.room_reached, entry.recorded_at))
