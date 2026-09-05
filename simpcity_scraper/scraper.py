import logging
from collections import defaultdict
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from simpcity_scraper.options import Options
from simpcity_scraper.session import Session
from simpcity_scraper.util import clean_url, get_domain_name
from simpcity_scraper.models import User, Media
from simpcity_scraper.domains import DOMAINS



class Scraper:
    def __init__(self) -> None:
        self._logger = logging.getLogger("Scraper")
        self._options = Options()
        self._session = Session()


    def run(self):
        for url in self._options.urls:
            url = clean_url(url)
            user = self.get_user(url)

            if user is None:
                self._logger.error(
                    f"Failed to get user for {url}"
                )

                continue

            medias = self.get_media_in_thread(url)
            self.pass_to_domains(medias, user)

    def pass_to_domains(self, medias: list[Media], user: User):
        domained_media: dict[str, list[Media]] = defaultdict(list)

        for media in medias:
            domained_media[media.domain_name].append(media)

        for domain_name, medias in domained_media.items():
            if domain_name not in DOMAINS.keys():
                continue

            domain_cls = DOMAINS[domain_name]
            domain_cls = domain_cls(
                user = user,
                medias = medias
            )
            domain_cls.start()


    def get_user(self, url: str) -> User | None:
        slug = url.split("/")[-1]
        id_str = slug.split(".")[-1]
        name = slug.split(".")[0]

        try:
            user_id = int(id_str)

        except ValueError:
            return None

        return User(
            name = name,
            url = url,
            user_id = user_id,
        )


    def get_max_page_count(self, page: BeautifulSoup) -> int:
        main_page_nav = page.find("ul", {"class": "pageNav-main"})

        if not main_page_nav:
            return 1

        page_navs = main_page_nav.find_all("li", {"class": "pageNav-page"})

        if not page_navs:
            return 1

        last_nav = page_navs[-1]

        try:
            return int(last_nav.get_text())

        except ValueError:
            return 1


    def get_media_in_thread(self, url: str) -> list[Media]:
        page = self._session.get_soup(url)

        if page is None:
            return []

        max_page_count = self.get_max_page_count(page)

        medias = []
        for page_num in range(1, max_page_count + 1):
            if page_num != 1:
                page = self._session.get_soup(
                    url = url + f"/page-{page_num}"
                )

            if page is None:
                self._logger.error(
                    f"Failed to get {url}/page-{page_num}"
                )
                return []

            media_in_page = self.get_media_in_page(page)

            if media_in_page:
                medias.extend(media_in_page)

        return medias


    def get_media_in_page(self, page: BeautifulSoup) -> list[Media]:
        def resolve_url_element(element: Tag) -> tuple[str, str] | None:
            href = element.get("href")

            if not isinstance(href, str):
                return None

            if "goonbox.cr/img/" in href:
                img_element = element.find("img")

                if not img_element:
                    return None

                src = img_element.get("src")

                if not isinstance(src, str):
                    return None

                href = src.replace(".md", "")

            domain_name = get_domain_name(href)
            if domain_name not in DOMAINS.keys():
                return None

            return href, domain_name

        post_cells = page.find_all("div", {"class": "message-cell--main"})
        medias: list[Media] = []

        for post_cell in post_cells:
            cell_content = post_cell.find("div", {"class": "message-userContent"})
            time_element = post_cell.find("time", {"class": "u-dt"})

            if (
                not cell_content
                or not time_element
            ):
                continue

            timestamp_str = time_element.get("data-timestamp")

            if not isinstance(timestamp_str, str):
                continue

            try:
                timestamp = int(timestamp_str)

            except ValueError:
                continue

            posted_at = datetime.fromtimestamp(timestamp)

            post_id_str = cell_content.get("data-lb-id")

            if not post_id_str:
                continue

            try:
                post_id = int(post_id_str.split("-")[-1])

            except ValueError:
                continue

            external_urls = cell_content.find_all("a", {"class": "link--external"})

            for external_url in external_urls:
                resolved = resolve_url_element(external_url)

                if resolved:
                    resolved_url, domain_name = resolved

                    medias.append(Media(
                        url = resolved_url,
                        domain_name = domain_name,
                        posted_at = posted_at,
                        post_id = post_id,
                    ))

        return medias