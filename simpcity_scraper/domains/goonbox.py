from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid3, NAMESPACE_URL

from simpcity_scraper.domains.domain import Domain
from simpcity_scraper.simpcity.models import ExternalURL


class GoonBox(Domain):
    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        super().__init__(
            *args,
            **kwargs
        )
    
    
    def on_task(self, external_url: ExternalURL) -> None:
        post_path = (
            self.user_path
            / external_url.posted.strftime("%Y")
            / external_url.posted.strftime("%m - %b")
        )
        
        if "/image" in external_url.url:
            return self.handle_item(
                external_url = external_url,
                post_path = post_path
            )
    
    
    def handle_album(self, external_url: ExternalURL) -> None:
        pass
    
    
    def handle_item(
            self,
            external_url: ExternalURL,
            post_path: Path,
    ) -> None:
        file_ext = Path(urlparse(external_url.url).path).suffix
        file_id = (
            str(uuid3(NAMESPACE_URL, external_url.url))
            .replace("-", "")[12:]
        )
        file_path = (
            post_path
            / (
                f"{external_url.posted.strftime('[%Y-%m-%d]')} {file_id}{file_ext}"
            )
        )
        
        self._session.download(
            url = external_url.url,
            destination = file_path,
        )