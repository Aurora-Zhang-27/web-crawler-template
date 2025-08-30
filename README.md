# Web Crawler Template

A configurable, modular Python web crawler framework.  
Designed for easily adding site-specific crawlers via small `examples/*_crawler.py` subclasses and YAML config files.

---

## 🚀 Features

- **Modular Core**
  - `core/utils.py`: rate limiting and retry decorators, logging utilities
  - `core/crawler.py`: `BaseCrawler` abstract class with fetch/parse/save workflow
  - `core/parser.py`: generic `extract_fields()` helper for CSS-selector-based extraction
- **Config-Driven**
  - Use a YAML file to specify site settings (URLs, selectors, pagination, output).
- **Example Implementations**
  - AI Litigation Database: `examples/ai_lit_config.yaml` + `examples/ai_lit_crawler.py`
  - Climate Litigation Database: `examples/climate_lit_config.yaml` + `examples/climate_lit_crawler.py`
- **Easy Extension**
  - Add a new site by creating a YAML config and a small `examples/my_site_crawler.py`.

---

## ⚙️ Prerequisites

- Python 3.8+ (3.10 recommended)
- Google Chrome (matching webdriver version) or Chromium
- `pip` and virtualenv recommended
- Optional: `webdriver-manager` (recommended) — it downloads the correct ChromeDriver automatically

---

## 📦 Installation
```bash
# clone the repo
git clone https://github.com/<your-username>/web-crawler-template.git
cd web-crawler-template

# create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# install dependencies
pip install -r requirements.txt
```
---

## 🔧 Quick Start

Run one of the example crawlers by passing the YAML config to run.py:
```bash
# AI Litigation example
python run.py --config examples/ai_lit_config.yaml

# Climate Litigation example
python run.py --config examples/climate_lit_config.yaml
```
Default output files and formats are defined inside each YAML config (commonly in data/).

---

## 🧭 How run.py works (high level)  
1.	Load YAML config.  
2.	Dynamically import the crawler class specified by crawler_class in the config.  
3.	Call fetch_list() → returns one or more list-page HTML strings.  
4.	Call parse_list(html_list) → returns a list of items/URLs to fetch.  
5.	For each item: call fetch_detail(item) and then parse_detail(html) to produce a dict.  
6.	Append results and call save(output_path) on the crawler.  
7.	Quit the webdriver if present.  
This flow is implemented generically in run.py so your crawler implementations only need to implement four methods:
```
fetch_list() -> list[str]
parse_list(html_list) -> list[item]
fetch_detail(item) -> str (HTML)
parse_detail(html) -> dict
```
---

## 🔨 Adding a New Site

1.	Copy the template: `cp config.yaml my_site_config.yaml`
2.	Edit my_site_config.yaml  
Fill in your site’s name, list URL, selectors, pagination or load-more settings, and output path.	
3.	Create a crawler subclass examples/my_site_crawler.py:
```
from core.crawler import BaseCrawler
from core.parser import extract_fields
from bs4 import BeautifulSoup
import time

class MySiteCrawler(BaseCrawler):
    def fetch_list(self):
        self.driver.get(self.config['start_url'])
        time.sleep(self.config.get('rate_limit', 1))
        return [self.driver.page_source]

    def parse_list(self, html_list):
        items = []
        for html in html_list:
            soup = BeautifulSoup(html, "html.parser")
            for el in soup.select(self.config['list_selector']):
                a = el.select_one("a")
                if a and a.get("href"):
                    items.append(a['href'])
        # return unique items
        return list(dict.fromkeys(items))

    def fetch_detail(self, url):
        self.driver.get(url)
        time.sleep(self.config.get('rate_limit', 1))
        return self.driver.page_source

    def parse_detail(self, html):
        # either use extract_fields with config['detail_selectors'] 
        # or parse manually and return a dict
        return extract_fields(html, self.config['detail_selectors'])
```
4.	Run your new crawler: `python run.py --config examples/my_site_config.yaml`

---
## 🔍 Troubleshooting
- **Only headers or empty CSV**  
- **run.py has a debug_page setting in config. If no list items are parsed, the first page HTML is saved there — open it and check selectors.**  
- **Try increasing rate_limit (allow scripts to load) or disabling --headless in the crawler while debugging.**  
- **Ensure list_selector is a valid CSS selector (avoid invalid tokens like post-* wildcards).**  
- **Invalid CSS selector error**  
- **Use valid selectors (e.g. article.case_bundle, not article.post-*.case_bundle). Tools like the browser devtools console can help test selectors.**  
    - Selenium/ChromeDriver compatibility
	- Keep Chrome and ChromeDriver versions compatible. webdriver-manager usually handles this, but occasionally update Chrome or the manager.
	- Duplicate entries
	- Ensure parse_list() returns unique URLs; use list(dict.fromkeys(items)) or set() to deduplicate.
	- Site uses JavaScript-heavy rendering
	- Increase wait times or use WebDriverWait with conditions (element presence, etc.). In some cases, requests + parsing won’t work because the HTML is dynamically injected client-side.
---
✅ Good Practices
- **Keep crawler code focused (single responsibility): list parsing, detail fetching, detail parsing.**  
- **Prefer config over code changes: define selectors and pagination in YAML when possible.**  
- **Log useful debugging info (URLs fetched, counts parsed, saved path).**  
- **Keep core/ utilities pure Python (no site-specific logic) and English-only comments for open-source sharing.**  
---
## 📂 Project Structure

```
web-crawler-template/
├── core/
│   ├── crawler.py           # BaseCrawler abstract class
│   ├── parser.py            # extract_fields() helper
│   └── utils.py             # rate_limit, retry decorators and logging setup
├── examples/
│   ├── ai_lit_config.yaml
│   ├── ai_lit_crawler.py
│   ├── climate_lit_config.yaml
│   └── climate_lit_crawler.py
├── data/                    # Output directory
├── config.yaml              # Config template
├── run.py                   # Command-line entry point
├── requirements.txt
├── README.md
└── LICENSE
```

---

## ⚠️ License & Usage

- This project is intended for educational and research purposes.
- Respect target site robots.txt and Terms of Service.
- The author assumes no liability for use of this code.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
