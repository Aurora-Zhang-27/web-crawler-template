from core.crawler import BaseCrawler
from core.parser import extract_fields
from bs4 import BeautifulSoup   # 别忘了这行
import requests

class AILitCrawler(BaseCrawler):
    def fetch_list(self):
        htmls = []
        start = self.config['pagination']['start_page']
        end = start + self.config['pagination']['max_pages']
        for page in range(start, end):
            url = self.config['list_url'].format(page=page)
            resp = requests.get(url)
            htmls.append(resp.text)
        return htmls

    def parse_list(self, html_list):
        items = []
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            for art in soup.select(self.config['list_selector']):
                link = art.select_one('a').get('href')
                items.append(link)
        return items

    def fetch_detail(self, url):
        resp = requests.get(url)
        return resp.text

    def parse_detail(self, html):
        return extract_fields(html, self.config['detail_selectors'])
