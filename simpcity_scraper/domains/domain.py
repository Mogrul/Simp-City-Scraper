import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from simpcity_scraper.models import User, Media
from simpcity_scraper.session import Session
from simpcity_scraper.options import Options


class Domain:
    def __init__(
            self,
            user: User,
            medias: list[Media],
            logger: logging.Logger | None = None,
    ):
        self._logger = logger if logger else logging.getLogger("Domain")
        self._user = user
        self._medias = medias
        self._session = Session()
        self._options = Options()
        self._executor = ThreadPoolExecutor(
            max_workers = self._options.concurrent_downloads
        )

        self._futures: list[Future] = []
        self._lock = threading.Lock()

        self.user_path = (
            self._options.download_location
            / self._user.name
        )


    def submit_task(self, media: Media) -> Future:
        future = self._executor.submit(
            self.on_task,
            media,
        )

        with self._lock:
            self._futures.append(future)

        return future


    def start(self) -> None:
        for media in self._medias:
            self.submit_task(media)

        index = 0

        while True:
            with self._lock:
                futures = self._futures[index:]

            if not futures:
                with self._lock:
                    if index == len(self._futures):
                        break

                continue

            for future in futures:
                index += 1

                try:
                    result = future.result()

                except Exception as e:
                    self._logger.exception(e)
                    continue

        self._executor.shutdown()
        return None


    def on_task(self, media: Media) -> None:
        return None


    def on_album(self, media: Media) -> None:
        return None


    def on_item(self, media: Media) -> None:
        return None