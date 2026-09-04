from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen = True)
class User:
    name: str
    url: str

@dataclass(frozen = True)
class ExternalURL:
    posted: datetime
    url: str
    domain_name: str
    post_id: int