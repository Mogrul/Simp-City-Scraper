from pathlib import Path
from argparse import ArgumentParser, Namespace

from simpcity_scraper.shared.singleton import SingletonMeta


class Args(metaclass = SingletonMeta):
    def __init__(self):
        _args = self._load_args()
        
        self.urls: list[str] = _args.urls
        self.debug: bool = _args.debug
        self.cookie_path = Path(_args.cookie_path)
        self.max_retries: int = _args.max_retries
        self.download_location = Path(_args.download_location)
        self.concurrent_downloads: int = _args.concurrent_downloads
        
        if not self.cookie_path.exists():
            print(f"Cookie file not found in {self.cookie_path}")
            
            import os
            os.abort()
    
    
    def _load_args(self) -> Namespace:
        parser = ArgumentParser()
        
        parser.add_argument(
            "urls",
            nargs = "+",
            help = "Urls to scrape from https://simpcity.cr"
        )
        
        parser.add_argument(
            "--cookie_path",
            default = ".cookies/simpcity.txt",
            help = "Path to simpcity.txt cookie file.",
        )
        
        parser.add_argument(
            "--debug",
            action = "store_true",
            help = "Enable debug logging."
        )
        
        parser.add_argument(
            "--max-retries",
            default = 5,
            help = "Amount of retries on HTTP 429 return code."
        )
        
        parser.add_argument(
            "--download-location",
            default = "Downloads",
            help = "Location where downloads will go."
        )
        
        parser.add_argument(
            "--concurrent-downloads",
            default = 10,
            help = "Amount of downloads to happen simultaenously."
        )
        
        return parser.parse_args()