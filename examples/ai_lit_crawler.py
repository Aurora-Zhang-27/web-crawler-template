import time
from typing import List, Dict
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from core.crawler import BaseCrawler

BASE_URL = "https://blogs.gwu.edu/law-eti/ai-litigation-database/"
UNWANTED_RESULTS = {"area of application", "and activity to date"}


def get_page_source(driver) -> str:
    try:
        return driver.page_source
    except Exception:
        handles = driver.window_handles
        if handles:
            driver.switch_to.window(handles[0])
            return driver.page_source
        return ""


def parse_dt_dd_pairs(dl) -> Dict[str, str]:
    data = {}
    last_dt = None
    for tag in dl.find_all(["dt", "dd"], class_=["cbResultSetListViewDataLabel", "cbResultSetData"]):
        if tag.name == "dt":
            last_dt = tag.get_text(strip=True)
        elif tag.name == "dd" and last_dt:
            txt = tag.get_text(strip=True)
            if not txt or txt == "\xa0":
                data[last_dt] = "NA"
            else:
                a = tag.find("a")
                if a and a.get("href"):
                    data[last_dt] = f"{a.get_text(strip=True)} ({a['href']})"
                else:
                    data[last_dt] = txt
            last_dt = None
    return data


class AILitCrawler(BaseCrawler):
    def __init__(self, config):
        super().__init__(config)
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.implicitly_wait(10)

    def fetch_list(self) -> List[str]:
        htmls = []
        self.driver.get(BASE_URL)
        time.sleep(self.config.get("rate_limit", 2))
        start = self.config.get("pagination", {}).get("start_page", 1)
        max_pages = self.config.get("pagination", {}).get("max_pages", 1)
        for _ in range(start, start + max_pages):
            htmls.append(self.driver.page_source)
            try:
                btn = self.driver.find_element("css selector", 'a.cbResultSetNavigationLinks[data-cb-name="JumpToNext"]')
                btn.click()
                time.sleep(self.config.get("rate_limit", 2))
            except Exception:
                break
        return htmls

    def parse_list(self, html_list: List[str]) -> List[str]:
        items = []
        for html in html_list:
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if not table:
                continue
            for row in table.find_all("tr")[1:]:
                a = row.find("a")
                if a and a.get("href"):
                    href = a["href"]
                    if not href.startswith("http"):
                        href = BASE_URL + href
                    items.append(href)
        return list(dict.fromkeys(items))

    def fetch_detail(self, url: str) -> str:
        self.driver.get(url)
        time.sleep(self.config.get("rate_limit", 1))
        return get_page_source(self.driver)

    def parse_detail(self, html: str) -> Dict:
        soup = BeautifulSoup(html, "html.parser")
        record = {}
        for dl in soup.find_all("dl", {"data-cb-name": "DataCtnr"}):
            record.update(parse_dt_dd_pairs(dl))

        # summary sections
        def find_section_text(key):
            hdr = soup.find(lambda t: t.name in ["h2", "h3"] and key in t.get_text(strip=True).lower())
            if hdr:
                nxt = hdr.find_next("article")
                if nxt:
                    return "\n".join(p.get_text(strip=True) for p in nxt.find_all("p")) or "NA"
            return None

        sf = find_section_text("facts and activity to date")
        if sf:
            record["Summary of Facts and Activity to Date"] = sf

        ss = find_section_text("significance")
        if ss:
            record["Summary of Significance"] = ss

        # dockets & documents
        # Dockets: look for header 'Dockets' then parse dl within its article
        dockets = []
        hdr = soup.find(lambda t: t.name in ["h2", "h3"] and "dockets" in t.get_text(strip=True).lower())
        if hdr:
            art = hdr.find_next("article")
            if art:
                for dl in art.find_all("dl", {"data-cb-name": "DataCtnr"}):
                    dockets.append(parse_dt_dd_pairs(dl))
        record["Dockets"] = dockets or "NA"

        docs = []
        hdrs = soup.find_all(lambda t: t.name in ["h2", "h3"] and "documents" in t.get_text(strip=True).lower())
        if hdrs:
            art = hdrs[-1].find_next("article")
            if art:
                for dl in art.find_all("dl", {"data-cb-name": "DataCtnr"}):
                    docs.append(parse_dt_dd_pairs(dl))
        record["Documents"] = docs or "NA"

        return record
