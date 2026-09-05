from dataclasses import dataclass
from datetime import datetime



@dataclass(frozen = True)
class User:
    name: str
    url: str
    user_id: int


@dataclass
class Media:
    url: str
    domain_name: str
    posted_at: datetime
    post_id: int