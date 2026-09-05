from simpcity_scraper.logger import load_logger
from simpcity_scraper.options import Options
from simpcity_scraper.scraper import Scraper



def main():
    options = Options()
    logger = load_logger(
        debug = options.debug,
    )
    scraper = Scraper()
    scraper.run()

if __name__ == "__main__":
    main()
