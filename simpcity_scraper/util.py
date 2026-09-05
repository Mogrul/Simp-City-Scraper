from urllib.parse import urlparse

import tldextract



class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


def format_bytes(amount: int) -> str:
    value = float(amount)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    two_path = "/".join(parsed.path.split("/")[:3])

    return (
        f"{parsed.scheme}://{parsed.netloc}{two_path}"
    )


def get_domain_name(url: str) -> str:
    extracted = tldextract.extract(url)

    return extracted.domain