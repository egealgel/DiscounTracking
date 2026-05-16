from .trendyol import TrendyolScraper
from .amazon import AmazonScraper
from .zara import ZaraScraper
from .hm import HMScraper
from .mango import MangoScraper
from .hepsiburada import HepsiburadaScraper
from .n11 import N11Scraper
from .beymen import BeymenScraper
from .boyner import BoynerScraper
from .superstep import SuperstepScraper
from .fashfed import FashfedScraper
from .sneaksup import SneaksupScraper
from .vakkorama import VakkoramaScraper
from .occasion import OccasionScraper
from .mediamarkt import MediaMarktScraper
from .atasunoptik import AtasunOptikScraper
from .houseofsuperstep import HouseOfSuperstepScraper

SCRAPERS = {
    "trendyol": TrendyolScraper,
    "amazon": AmazonScraper,
    "zara": ZaraScraper,
    "hm": HMScraper,
    "mango": MangoScraper,
    "hepsiburada": HepsiburadaScraper,
    "n11": N11Scraper,
    "beymen": BeymenScraper,
    "boyner": BoynerScraper,
    "superstep": SuperstepScraper,
    "fashfed": FashfedScraper,
    "sneaksup": SneaksupScraper,
    "vakkorama": VakkoramaScraper,
    "occasion": OccasionScraper,
    "mediamarkt": MediaMarktScraper,
    "atasunoptik": AtasunOptikScraper,
    "houseofsuperstep": HouseOfSuperstepScraper,
}


def detect_site(url: str) -> str | None:
    url_lower = url.lower()
    if "trendyol.com" in url_lower:
        return "trendyol"
    if "amazon.com" in url_lower or "amazon.de" in url_lower or "amazon.co.uk" in url_lower or "amazon.fr" in url_lower:
        return "amazon"
    if "zara.com" in url_lower:
        return "zara"
    if "hm.com" in url_lower:
        return "hm"
    if "mango.com" in url_lower:
        return "mango"
    if "hepsiburada.com" in url_lower:
        return "hepsiburada"
    if "n11.com" in url_lower:
        return "n11"
    if "beymen.com" in url_lower:
        return "beymen"
    if "boyner.com.tr" in url_lower:
        return "boyner"
    if "houseofsuperstep.com" in url_lower:
        return "houseofsuperstep"
    if "superstep.com.tr" in url_lower:
        return "superstep"
    if "fashfed.com" in url_lower:
        return "fashfed"
    if "sneaksup.com" in url_lower:
        return "sneaksup"
    if "vakkorama.com" in url_lower:
        return "vakkorama"
    if "occasion.com.tr" in url_lower:
        return "occasion"
    if "mediamarkt.com.tr" in url_lower:
        return "mediamarkt"
    if "atasunoptik.com.tr" in url_lower:
        return "atasunoptik"
    return None


def get_scraper(site: str):
    return SCRAPERS.get(site)
