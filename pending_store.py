# pending_store.py
import uuid
from datetime import datetime, timedelta

class PendingStore:
    def __init__(self):
        self._data = {}  # intake_id -> payload
        self._ttl = timedelta(minutes=30)

    def create(self, payload):
        intake_id = str(uuid.uuid4())
        self._data[intake_id] = {"created_at": datetime.utcnow(), **payload}
        return intake_id

    def get(self, intake_id):
        item = self._data.get(intake_id)
        if not item:
            return None
        # optional TTL cleanup
        if datetime.utcnow() - item["created_at"] > self._ttl:
            self._data.pop(intake_id, None)
            return None
        return item

    def update(self, intake_id, updates):
        if intake_id not in self._data:
            return None
        self._data[intake_id].update(updates)
        return self._data[intake_id]

    def pop(self, intake_id):
        return self._data.pop(intake_id, None)

PENDING = PendingStore()
