import scrapy 
from scrapy.crawler import CrawlerProcess
from teknokent_scraper.teknokent_scraper.spiders.ankarauni_teknokent_spider import AnkaraUniSpider
from teknokent_scraper.teknokent_scraper.spiders.odtu_teknokent import OdtuSpider
from teknokent_scraper.teknokent_scraper.spiders.itu_teknkent_spider import ItuSpider
from teknokent_scraper.teknokent_scraper.spiders.hacettepe_teknokent_spider import HacettepeSpider
from teknokent_scraper.teknokent_scraper.spiders.gazi_teknokent_spider import GaziSpider
from teknokent_scraper.teknokent_scraper.spiders.bilkent_teknokent_spider import BilkentSpider


def main():
    crawler = CrawlerProcess()
    crawler.crawl(AnkaraUniSpider)
    crawler.crawl(OdtuSpider)
    crawler.crawl(ItuSpider)
    crawler.crawl(HacettepeSpider)
    crawler.crawl(GaziSpider)
    crawler.crawl(BilkentSpider)
    
    crawler.start()


if __name__ == "__main__":
    main()
