import logging
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid3, NAMESPACE_DNS

from simpcity_scraper.domains.domain import Domain
from simpcity_scraper.models import Media
from simpcity_scraper.util import clean_url


class GoonBox(Domain):
    def __init__(
            self,
            *args,
            **kwargs,
    ):
        super().__init__(
            logger = logging.getLogger("Domain.GoonBox"),
            *args,
            **kwargs,
        )


    def on_task(self, media: Media) -> None:
        if "/img/" in media.url:
            self.on_item(media)

            return None

        if "cuckcapital" in media.url:
            self.on_item(media)

            return None

        if "/a/" in media.url:
            self.on_album(media)

        return None


    def on_album(self, media: Media) -> None:
        album_images = []
        url = clean_url(media.url)
        album_id = url.split(".")[-1]
        api_url = f"https://goonbox.cr/api/albums/{album_id}/images"

        response = self._session.get_json(
            url = api_url,
            params = {
                "page": 1
            }
        )

        if response is None:
            return None

        images = response.get("images")
        pagination = response.get("pagination")

        if (
            not isinstance(images, list)
            or not isinstance(pagination, dict)
        ):
            return None

        max_page = pagination.get("last_page")
        album_images.extend(images)

        if not isinstance(max_page, int):
            return None

        for page_num in range(1, max_page + 1):
            if page_num == 1:
                continue

            response = self._session.get_json(
                url = api_url,
                params = {
                    "page": page_num
                }
            )

            if response is None:
                return None

            images = response.get("images")

            if not isinstance(images, list):
                return None

            album_images.extend(images)

        for image in images:
            original_url = image.get("original_url")

            if not isinstance(original_url, str):
                continue

            self.submit_task(Media(
                url = original_url,
                domain_name = media.domain_name,
                posted_at = media.posted_at,
                post_id = media.post_id,
            ))

        return None


    def on_item(self, media: Media) -> None:
        post_path = (
            self.user_path
            / media.posted_at.strftime("%Y")
            / media.posted_at.strftime("%m - %b")
        )
        file_id = (
            str(uuid3(NAMESPACE_DNS, media.url))
            .replace("-", "")[:12]
        )
        file_ext = (
            Path(
                urlparse(media.url)
                .path
            )
            .suffix
        )
        file_path = (
            post_path
            / (
                f"[{media.posted_at.strftime('%Y-%m-%d')}] "
                f"{file_id}{file_ext}"
            )
        )

        self._session.download(
            url = media.url,
            destination = file_path
        )

        return None