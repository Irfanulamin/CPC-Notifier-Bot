"""
SeenTracker — persists sent notification keys to MongoDB so the bot
survives restarts without re-sending old alerts.

Collection: cp_notifier.seen  /  cp_notifier.reminded
Documents:  { _id: "new:codeforces-1234", ts: <datetime> }
"""

import logging
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os

log = logging.getLogger(__name__)


class SeenTracker:
    def __init__(self, namespace: str = "seen"):
        """
        namespace: collection name — use "seen" for new-contest keys,
                   "reminded" for reminder keys.
        """
        uri = os.environ.get("MONGODB_URI", "").strip()
        if not uri:
            raise ValueError("MONGODB_URI is not set. Add it to your .env file.")
        self._col = MongoClient(uri)["cp_notifier"][namespace]

    def is_new(self, key: str) -> bool:
        try:
            return self._col.find_one({"_id": key}) is None
        except PyMongoError as e:
            log.error(f"[SeenTracker] MongoDB read error for key={key}: {e}")
            return False  # fail safe — don't re-send if DB is down

    def mark(self, key: str) -> None:
        try:
            self._col.update_one(
                {"_id": key},
                {"$setOnInsert": {"_id": key, "ts": datetime.now(timezone.utc)}},
                upsert=True,
            )
        except PyMongoError as e:
            log.error(f"[SeenTracker] MongoDB write error for key={key}: {e}")
