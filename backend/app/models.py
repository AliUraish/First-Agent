import json
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class User:
    email: str
    credentials: Dict

    @classmethod
    def from_db_row(cls, row):
        if row is None:
            return None
        return cls(
            email=row['email'],
            credentials=json.loads(row['credentials'])
        )

    def to_db_dict(self):
        return {
            'email': self.email,
            'credentials': json.dumps(self.credentials)
        } 