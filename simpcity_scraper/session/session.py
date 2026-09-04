from http.cookiejar import MozillaCookieJar
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from simpcity_scraper.shared.args import Args
from simpcity_scraper.shared.singleton import SingletonMeta
from simpcity_scraper.shared.util import format_bytes


class Session(metaclass = SingletonMeta):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._args = Args()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0"
                " (Windows NT 10.0; Win64; x64; rv:154.0)"
                " Gecko/20100101"
                " Firefox/154.0"
            )
        })
        
        jar = MozillaCookieJar()
        jar.load(
            str(self._args.cookie_path),
            ignore_discard = True,
            ignore_expires = True
        )
        
        self._session.cookies.update(jar)
    
    
    def get_soup(
            self,
            url: str,
            headers: dict[str, str] | None = None,
            params: dict[str, str] | None = None
    ) -> BeautifulSoup | int | None:
        if headers is None:
            headers = {}
        
        if params is None:
            params = {}
        
        try:
            response = self._session.get(
                url = url,
                params = params,
                headers = headers,
                timeout = 10,
            )
            
            self._logger.debug(
                f"{response.status_code}: {url}"
            )
        
        except requests.exceptions.Timeout:
            self._logger.error(
                f"Request timed out: {url}"
            )
            
            return None
        
        if response.status_code != 200:
            self._logger.error(
                f"Returned status code {response.status_code} from {url}"
            )
            
            return response.status_code
        
        return BeautifulSoup(response.text, "html.parser")
    
    
    def download(
            self,
            url: str,
            destination: Path,
            headers: dict[str, str] | None = None,
            params: dict[str, str] | None = None,
    ) -> None:
        if headers is None:
            headers = {}
        
        if params is None:
            params = {}
        
        if destination.exists():
            self._logger.warning(
                f"[EXISTS] {url} -> {destination}"
            )
            
            return None
        
        temp_destination = destination.with_suffix(
            destination.suffix + ".temp"
        )
        downloaded_bytes = 0
        
        if temp_destination.exists():
            downloaded_bytes = temp_destination.stat().st_size
            headers["Range"] = f"bytes={downloaded_bytes}-"
        
        temp_destination.parent.mkdir(
            parents = True,
            exist_ok = True,
        )
        
        with self._session.get(
                url = url,
                headers = headers,
                params = params,
                timeout = 10,
                stream = True,
        ) as response:
            if response.status_code not in (200, 203):
                self._logger.error(
                    f"{response.status_code}: {url}"
                )
                
                return None

            if downloaded_bytes and response.status_code == 200:
                downloaded_bytes = 0
                temp_destination.unlink(missing_ok = True)
            
            mode = "ab" if downloaded_bytes else "wb"
            
            with open(temp_destination, mode) as f:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
        
        if destination.exists():
            temp_destination.unlink()
            return None
        
        if not temp_destination.exists():
            return None
        
        downloaded_bytes = temp_destination.stat().st_size
        temp_destination.rename(destination)
        
        self._logger.info(
            f"{format_bytes(downloaded_bytes)} - {destination}"
        )
        
        return None