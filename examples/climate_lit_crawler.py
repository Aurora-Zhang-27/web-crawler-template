from core.crawler import BaseCrawler
from core.parser import extract_fields
from bs4 import BeautifulSoup
import requests

class ClimateLitCrawler(BaseCrawler):
    def fetch_list(self):
        items = []
        offset = self.config['list_payload']['offset']
        step = self.config['load_more']['step']
        max_items = self.config['load_more']['max_items']

        while offset < max_items:
            payload = {'offset': offset, 'limit': step}
            resp = requests.post(self.config['list_url'], json=payload)
            data = resp.json()  # 如果接口返回 JSON
            # 假设 data['entries'] 是 HTML 字符串列表
            for html in data.get('entries', []):
                items.append(html)
            offset += step
        return items

    def parse_list(self, html_list):
        urls = []
        for html in html_list:
            soup = BeautifulSoup(html, 'html.parser')
            for entry in soup.select(self.config['list_selector']):
                link = entry.select_one('a').get('href')
                urls.append(link)
        return urls

    def fetch_detail(self, url):
        resp = requests.get(url)
        return resp.text

    def parse_detail(self, html):
        # 如果有多个文档链接，返回列表
        data = extract_fields(html, self.config['detail_selectors'])
        docs = BeautifulSoup(html, 'html.parser').select(self.config['detail_selectors']['documents'])
        data['documents'] = [a.get('href') for a in docs]
        return data
