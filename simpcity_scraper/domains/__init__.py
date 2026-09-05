from simpcity_scraper.domains.domain import Domain
from simpcity_scraper.domains.goonbox import GoonBox


DOMAINS: dict[str, type[Domain]] = {
    "goonbox": GoonBox,
    "cuckcapital": GoonBox,
}