"""
Tiny pluggable session store.
Swap MemorySessionStore for RedisSessionStore, SQLSessionStore …
"""

from collections import defaultdict
from typing import List, Dict

Chat = List[Dict[str, str]]  # OpenAI-style [{role, content}, ...]

class SessionStore:
    def add(self, sid: str, message: Dict[str, str]) -> None: ...
    def get(self, sid: str) -> Chat | None: ...
    def new(self, sid: str, first_msg: Dict[str, str]) -> None: ...

class MemorySessionStore(SessionStore):
    _store: Dict[str, Chat] = defaultdict(list)

    def add(self, sid: str, message: Dict[str, str]) -> None:
        self._store[sid].append(message)

    def get(self, sid: str) -> Chat | None:
        return self._store.get(sid)

    def new(self, sid: str, first_msg: Dict[str, str]) -> None:
        self._store[sid] = [first_msg]
