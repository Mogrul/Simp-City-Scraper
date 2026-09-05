import logging
from http.cookiejar import MozillaCookieJar
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from simpcity_scraper.options import Options
from simpcity_scraper.util import format_bytes, SingletonMeta



class Session(metaclass = SingletonMeta):
    def __init__(self):
        self._session = requests.Session()
        self._logger = logging.getLogger("Session")
        self._options = Options()

        self.update_headers()
        self.update_cookies()


    def update_headers(self):
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64; rv:154.0) "
                "Gecko/20100101 "
                "Firefox/154.0"
            )
        })


    def update_cookies(self):
        cookie_file = self._options.cookie_path

        jar = MozillaCookieJar()
        jar.load(
            filename = str(cookie_file),
            ignore_discard = True,
            ignore_expires = True,
        )

        self._session.cookies.update(jar)


    def get_json(
            self,
            url: str,
            params: dict[str, str] | None = None,
    ) -> dict | None:
        if params is None:
            params = {}

        try:
            response = self._session.get(
                url = url,
                params = params,
                timeout = 10,
            )

            self._logger.debug(
                f"{f'[{response.status_code}]':<20} {url}"
            )

        except requests.exceptions.Timeout:
            self._logger.warning(
                f"{'[TIMEOUT]':<20} {url}"
            )

            return None

        if response.status_code != 200:
            return None

        try:
            return response.json()

        except requests.exceptions.JSONDecodeError:
            self._logger.error(
                f"Failed to return JSON response from {response.url}"
            )
            return None


    def get_soup(
            self,
            url: str,
            params: dict[str, str] | None = None,
            headers: dict[str, str] | None = None,
    ) -> BeautifulSoup | None:
        if params is None:
            params = {}

        if headers is None:
            headers = {}

        try:
            response = self._session.get(
                url = url,
                headers = headers,
                params = params,
                timeout = 10,
            )

            self._logger.debug(
                f"{f'[{response.status_code}]':<20} {url}"
            )

        except requests.exceptions.Timeout:
            self._logger.warning(
                f"{'[TIMEOUT]':<20} {url}"
            )

            return None

        if response.status_code != 200:
            return None

        return BeautifulSoup(response.text, "html.parser")


    def download(
            self,
            url: str,
            destination: Path,
    ):
        if destination.exists():
            self._logger.debug(
                f"{f'[EXISTS]':<20} {url}"
            )

            return None

        headers = {}
        temp_destination = destination.with_suffix(destination.suffix + ".temp")
        downloaded_bytes = 0

        if temp_destination.exists():
            downloaded_bytes = temp_destination.stat().st_size
            headers["Range"] = f"bytes={downloaded_bytes}-"

        temp_destination.parent.mkdir(
            parents = True,
            exist_ok = True,
        )

        try:
            with self._session.get(
                url = url,
                headers = headers,
                stream = True,
            ) as response:
                if response.status_code not in (200, 206, 203):
                    self._logger.error(
                        f"{f'[{response.status_code}]'} {url}"
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

        except requests.exceptions.Timeout:
            self._logger.error(
                f"{f'[TIMEOUT]':<20} {url}"
            )

            return None

        downloaded_bytes = temp_destination.stat().st_size
        if (
            temp_destination.exists()
            and not destination.exists()
        ):
            temp_destination.rename(destination)

        else:
            return None

        self._logger.info(
            f"{format_bytes(downloaded_bytes):<20} | {destination}"
        )

        return None