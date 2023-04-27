from abc import ABC
from datetime import datetime
from uuid import UUID, uuid4


class Storable(ABC):
    id: UUID
    saved_at: datetime

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = uuid4()
        self.saved_at = datetime.now()

    def update_timestamp(self):
        self.saved_at = datetime.now()
