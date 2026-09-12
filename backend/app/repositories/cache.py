from __future__ import annotations
import json, sqlite3, threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass
class CacheEntry:
    payload: Any
    retrieved_at: datetime
    expires_at: datetime
    @property
    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

class CacheRepository:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS cache_entries(namespace TEXT,key TEXT,payload TEXT,retrieved_at TEXT,expires_at TEXT,PRIMARY KEY(namespace,key))")
            db.execute("CREATE TABLE IF NOT EXISTS source_health(source TEXT PRIMARY KEY,state TEXT,last_success_at TEXT,message TEXT)")

    def _connect(self): return sqlite3.connect(self.path)
    def put(self, namespace: str, key: str, payload: Any, retrieved_at: datetime, expires_at: datetime) -> None:
        with self._lock, self._connect() as db:
            db.execute("INSERT OR REPLACE INTO cache_entries VALUES(?,?,?,?,?)", (namespace,key,json.dumps(payload,default=str),retrieved_at.isoformat(),expires_at.isoformat()))
    def get(self, namespace: str, key: str) -> CacheEntry | None:
        with self._lock, self._connect() as db:
            row=db.execute("SELECT payload,retrieved_at,expires_at FROM cache_entries WHERE namespace=? AND key=?",(namespace,key)).fetchone()
        if not row: return None
        return CacheEntry(json.loads(row[0]), datetime.fromisoformat(row[1]), datetime.fromisoformat(row[2]))
    def set_health(self, source: str, state: str, last_success_at: datetime | None, message: str | None):
        with self._lock, self._connect() as db:
            db.execute("INSERT OR REPLACE INTO source_health VALUES(?,?,?,?)",(source,state,last_success_at.isoformat() if last_success_at else None,message))
    def get_health(self, source: str):
        with self._lock, self._connect() as db:
            return db.execute("SELECT state,last_success_at,message FROM source_health WHERE source=?",(source,)).fetchone()
