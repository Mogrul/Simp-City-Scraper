from simpcity_scraper.shared.logger import load_logger
from simpcity_scraper.shared.args import Args
from simpcity_scraper.simpcity.simpcity import SimpCity

def main():
    args = Args()
    logger = load_logger(args.debug)
    
    simpcity = SimpCity()
    simpcity.run()


if __name__ == "__main__":
    main()
