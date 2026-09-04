from collections import defaultdict
from datetime import datetime
import logging
from urllib.parse import urlparse
import time

from bs4 import BeautifulSoup, Tag
import tldextract

from simpcity_scraper.session.session import Session
from simpcity_scraper.simpcity.models import User, ExternalURL
from simpcity_scraper.shared.args import Args
from simpcity_scraper.domains import DOMAIN_NAMES, DOMAINS


def get_domain_name(url: str) -> str:
    extracted = tldextract.extract(url)
    
    return extracted.domain


def get_domain(domain_name: str):
    return next(
        (
            domain_class
            for domain_names, domain_class in DOMAINS.items()
            if domain_name in domain_names
        ),
        None,
    )

class SimpCity:
    def __init__(self) -> None:
        self._session = Session()
        self._logger = logging.getLogger(__name__)
        self._args = Args()
    
    
    def run(self):
        for url in self._args.urls:
            if "/threads/" not in url:
                continue
            
            parsed = urlparse(url)
            user_path = (
                parsed
                .path
                .split("/threads/")[1]
                .split("/")[0]
            )
            user_name = (
                user_path
                .split(".")[0]
                .replace("-", " ")
                .title()
            )
            url = (
                f"{parsed.scheme}://{parsed.netloc}/threads/{user_path}"
            )
            
            user = User(
                name = user_name,
                url = url,
            )
            
            external_urls = self.get_external_urls(url)

            if not external_urls:
                self._logger.warning(
                    f"Couldn't find any compatible posts in {url}"
                )
                continue
            
            self._logger.info(
                f"Found {len(external_urls)} compatible URLs in {url}"
            )
            
            self.pass_to_domains(
                user = user,
                external_urls = external_urls
            )
    
    
    def pass_to_domains(
            self,
            user: User,
            external_urls: list[ExternalURL]
    ):
        external_domain_urls: dict[str, list[ExternalURL]] = defaultdict(list)
        
        for external_url in external_urls:
            external_domain_urls[external_url.domain_name].append(external_url)
    
        for domain_name, domained_urls in external_domain_urls.items():
            if not domain_name in DOMAIN_NAMES:
                continue
            
            domain_cls = get_domain(domain_name)
            
            if not domain_cls:
                continue
            
            domain_cls = domain_cls(
                external_urls = domained_urls,
                user = user,
            )
            domain_cls.start()
    
    
    def get_external_urls(
            self,
            url: str
    ) -> list[ExternalURL]:
        def get_max_page_count(page: BeautifulSoup) -> int:
            nav_main = page.find("ul", {"class": "pageNav-main"})
            
            if nav_main is None:
                return 1
            
            navs = nav_main.find_all("li", {"class": "pageNav-page"})
            
            if not navs:
                return 1
            
            last_nav = navs[-1]
            last_nav_text = last_nav.get_text()
            
            try:
                return int(last_nav_text)
            
            except ValueError:
                return 1
        
        external_urls = []
        page = self._session.get_soup(url)
        
        if (
            isinstance(page, int)
            and page != 200
        ):
            return []
        
        if not isinstance(page, BeautifulSoup):
            return []
               
        max_page_count = get_max_page_count(page)
        
        for page_num in range(1, max_page_count + 1):
            paged_url = ""
            if page_num != 1:
                paged_url = url + f"/page-{page_num}"
                page = self._session.get_soup(paged_url)
            
            if page == 429:
                tries = 0
                while True:
                    tries += 1
                    
                    if tries > self._args.max_retries:
                        self._logger.error(
                            f"Max retries exceeded for {paged_url}"
                        )
                        
                        return []
                    
                    self._logger.warning(
                        f"[{tries}/{self._args.max_retries}] 429 received from {paged_url}, waiting 2 seconds..."
                    )
                    
                    time.sleep(2)
                    
                    page = self._session.get_soup(paged_url)
                    
                    if not isinstance(page, int):
                        break
            
            if not isinstance(page, BeautifulSoup):
                return []
            
            external_urls.extend(
                self.get_external_urls_in_page(page)
            )
        
        return external_urls
    
    
    def get_external_urls_in_page(
            self,
            page: BeautifulSoup,
    ) -> list[ExternalURL]:
        def handle_external(external_element: Tag) -> tuple[str, str] | None:
            href = external_element.get("href")
            
            if not isinstance(href, str):
                return None
            
            # GoonBox.cr resolving
            if (
                "goonbox.cr" in href
                and "/img/" in href
            ):
                img_element = external_element.find("img")
                
                if not img_element:
                    return None
                
                href = img_element.get("src")
                
                if not isinstance(href, str):
                    return None
                
                if ".md." in href:
                    href = href.replace(".md", "")
            
            domain_name = get_domain_name(href)
                        
            if domain_name not in DOMAIN_NAMES:
                return None
            
            return href, domain_name
        
        external_urls = []
        post_articles = page.find_all("article", {"class": "message--post"})
        
        for post_article in post_articles:
            post_id = post_article.get("data-content")
            
            if not isinstance(post_id, str):
                continue
            
            post_id = post_id.replace("post-", "")
            
            try:
                post_id = int(post_id)
            
            except ValueError:
                continue
            
            post_cell = post_article.find("div", {"class": "message-cell--main"})
            
            if not post_cell:
                continue

            time_element = post_cell.find("time", {"class": "u-dt"})
            
            if not time_element:
                continue
            
            post_timestamp = time_element.get("data-timestamp")
            
            if not isinstance(post_timestamp, str):
                continue
            
            try:
                post_posted = datetime.fromtimestamp(int(post_timestamp))
            
            except KeyError:
                continue
            
            external_elements = post_cell.find_all("a", {"class": "link--external"})
            
            for external_element in external_elements:
                external_url = handle_external(external_element)
                
                if external_url is None:
                    continue
                
                external_url, external_url_domain_name = external_url
                
                external_urls.append(ExternalURL(
                    posted = post_posted,
                    url = external_url,
                    domain_name = external_url_domain_name,
                    post_id = post_id
                ))
        
        return external_urls