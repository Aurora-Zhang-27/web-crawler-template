import time
from urllib.parse import urljoin
import logging
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

from core.crawler import BaseCrawler
# optional: from core.parser import extract_fields

logger = logging.getLogger("ClimateLitCrawler")


class ClimateLitCrawler(BaseCrawler):
    """
    Climate Litigation crawler (example).
    Fetches a list page, extracts article entries and visits details.
    """

    def __init__(self, config):
        super().__init__(config)
        service = Service(ChromeDriverManager().install())
        opts = webdriver.ChromeOptions()
        # If headless misses dynamic content, run without headless while debugging
        # opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.implicitly_wait(10)

    def fetch_list(self) -> List[str]:
        htmls = []
        start_url = self.config.get("start_url") or self.config.get("list_url")
        if not start_url:
            logger.error("start_url is not set in config")
            return htmls
        logger.info("Loading list URL: %s", start_url)
        self.driver.get(start_url)
        time.sleep(self.config.get("rate_limit", 2))
        htmls.append(self.driver.page_source)
        return htmls

    def parse_list(self, html_list: List[str]) -> List[str]:
        selector = self.config.get("list_selector", "article")
        items: List[str] = []
        for html in html_list:
            # parse only structural tags to speed up
            soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("article"))
            # If CSS selector is invalid for soupsieve, fall back to "article"
            try:
                cards = soup.select(selector)
            except Exception:
                logger.warning("Invalid selector %s — falling back to 'article'", selector)
                cards = soup.find_all("article")
            for card in cards:
                # try several possible link locations
                a = card.select_one("h2.entry-title a, h2.facetwp-template-title a, a.facetwp-title, a")
                if a and a.has_attr("href"):
                    href = a["href"].strip()
                    base = self.config.get("start_url") or self.config.get("list_url")
                    if base:
                        href = urljoin(base, href)
                    items.append(href)
        # deduplicate preserving order
        return list(dict.fromkeys(items))

    def fetch_detail(self, url: str) -> str:
        if not isinstance(url, str) or not url.strip():
            logger.warning("fetch_detail received invalid url: %r", url)
            return ""
        try:
            self.driver.get(url)
            time.sleep(self.config.get("rate_limit", 1))
            return self.driver.page_source
        except Exception as e:
            logger.exception("Error loading detail url %s: %s", url, e)
            return ""

    def parse_detail(self, html: str) -> dict:
        # If you have core.parser.extract_fields available and configured, prefer it:
        selectors = self.config.get("detail_selectors")
        try:
            from core.parser import extract_fields

            if selectors:
                out = extract_fields(html, selectors)
                if isinstance(out, dict) and any(out.values()):
                    return out
        except Exception:
            # fall back to manual parse
            pass

        soup = BeautifulSoup(html, "html.parser")
        def pick_one(*sels):
            for s in sels:
                el = soup.select_one(s)
                if el and el.get_text(strip=True):
                    return el.get_text(strip=True)
            return ""

        title = pick_one("h1.entry-title", "h1.node-title", "h2.facetwp-template-title")
        filed_date = pick_one("div.field--name-field-filed span.highlight", "div.entry-meta-item.filing-date span.highlight")
        status = pick_one("div.field--name-field-status span.highlight", "div.entry-meta-item.status span.highlight")
        court = pick_one("div.field--name-field-court span.highlight", "div.entry-meta-item.court span.highlight")
        description = pick_one("div.field--name-field-summary p", "div.field--name-field-description p", ".entry-content p")

        return {
            "title": title or "NA",
            "filed_date": filed_date or "NA",
            "status": status or "NA",
            "court": court or "NA",
            "description": description or "NA",
            "detail_url": self.config.get("start_url", "")
        }
