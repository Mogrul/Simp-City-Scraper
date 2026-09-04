import logging
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Condition
from pathlib import Path

from simpcity_scraper.simpcity.models import ExternalURL, User
from simpcity_scraper.shared.args import Args
from simpcity_scraper.session.session import Session


class Domain:
    def __init__(
            self,
            external_urls: list[ExternalURL],
            user: User,
            logger: logging.Logger | None = None
    ):
        self._logger = (
            logger if logger 
            else logging.getLogger(__name__)
        )
        self._args = Args()
        self._session = Session()
        
        self.user = user
        self.external_urls = external_urls
        self.user_path = (
            self._args.download_location
            / self.user.name
        )
        
        self._executor = ThreadPoolExecutor(
            max_workers = self._args.concurrent_downloads
        )
        self._condition = Condition()
        self._pending = 0
        self._results = []
    
    
    def submit(self, fn, *args, **kwargs):
        with self._condition:
            self._pending += 1
        
        future = self._executor.submit(fn, *args, **kwargs)
        future.add_done_callback(self._task_done)
    
    
    def _task_done(self, future: Future):
        try:
            result = future.result()
        
            with self._condition:
                self._results.append(result)
        
        finally:
            with self._condition:
                self._pending -= 1
                
                if self._pending == 0:
                    self._condition.notify_all()
    
    
    def start(self):
        for external_url in self.external_urls:
            self.submit(self.on_task, external_url)
        
        with self._condition:
            while self._pending > 0:
                self._condition.wait()
        
        return self._results
    
    
    def on_task(self, external_url: ExternalURL) -> None:
        pass
    
    
    def handle_album(self, external_url: ExternalURL) -> None:
        pass
        
        
    def handle_item(
            self,
            external_url: ExternalURL,
            post_path: Path,
    ) -> None:
        pass