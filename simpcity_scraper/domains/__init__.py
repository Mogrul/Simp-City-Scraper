from simpcity_scraper.domains.domain import Domain
from simpcity_scraper.domains.goonbox import GoonBox


DOMAINS: dict[tuple[str, ...], type[Domain]] = {
    ("goonbox", "cuckcapital"): GoonBox
}

DOMAIN_NAMES = [
    domain_name
    for domain_group in DOMAINS
    for domain_name in domain_group
]