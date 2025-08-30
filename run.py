from __future__ import annotations

import argparse
import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("run")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a configured crawler")
    p.add_argument("-c", "--config", required=True, help="Path to YAML config file")
    return p.parse_args()


def load_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ensure_parent_dir(path: Optional[str]) -> None:
    if not path:
        return
    parent = Path(path).parent
    if parent and not parent.exists():
        logger.info("Creating directory: %s", parent)
        parent.mkdir(parents=True, exist_ok=True)


def instantiate_crawler(config: Dict[str, Any]):
    full = config.get("crawler_class")
    if not full:
        raise KeyError("crawler_class is missing in config")
    module_name, class_name = full.rsplit(".", 1)
    module = importlib.import_module(module_name)
    CrawlerClass = getattr(module, class_name)
    return CrawlerClass(config)


def main() -> None:
    args = parse_args()
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.exception("Failed to load config: %s", e)
        return

    output = config.get("output_path") or config.get("output") or "data/output.csv"
    ensure_parent_dir(output)

    try:
        crawler = instantiate_crawler(config)
    except Exception as e:
        logger.exception("Failed to instantiate crawler: %s", e)
        return

    if not hasattr(crawler, "results") or crawler.results is None:
        crawler.results = []

    # 1) fetch list pages
    try:
        html_list = crawler.fetch_list()
        if not isinstance(html_list, list):
            html_list = [html_list] if html_list else []
    except Exception:
        logger.exception("fetch_list() failed")
        html_list = []

    logger.info("Fetched %d list page(s)", len(html_list))

    # 2) parse list -> items (urls)
    try:
        items = crawler.parse_list(html_list)
        if items is None:
            items = []
    except Exception:
        logger.exception("parse_list() failed")
        items = []

    # Save debug page if no items parsed
    if not items and html_list:
        debug_path = config.get("debug_page") or "data/debug_page1.html"
        ensure_parent_dir(debug_path)
        try:
            Path(debug_path).write_text(html_list[0], encoding="utf-8")
            logger.warning("No items parsed — wrote debug page to %s", debug_path)
        except Exception:
            logger.exception("Failed to write debug page")

    logger.info("Parsed %d items", len(items))

    # 3) fetch detail pages and parse
    for idx, item in enumerate(items, start=1):
        logger.info("[%d/%d] Processing %s", idx, len(items), repr(item))
        if not isinstance(item, (str,)):
            logger.warning("Skipping non-string item: %r", item)
            continue
        try:
            html_detail = crawler.fetch_detail(item)
        except Exception:
            logger.exception("fetch_detail failed for %s", item)
            continue

        if not html_detail:
            logger.warning("Empty detail HTML for %s", item)
            continue

        try:
            rec = crawler.parse_detail(html_detail)
        except Exception:
            logger.exception("parse_detail failed for %s", item)
            continue

        if isinstance(rec, dict):
            crawler.results.append(rec)
        elif isinstance(rec, list):
            crawler.results.extend(rec)
        else:
            logger.warning("parse_detail returned unsupported type %s for %s", type(rec), item)

    # 4) save
    try:
        ensure_parent_dir(output)
        crawler.save(output)
        logger.info("Saved %d records to %s", len(crawler.results), output)
    except Exception:
        logger.exception("Failed to save results")

    # 5) quit driver
    try:
        if hasattr(crawler, "driver"):
            crawler.driver.quit()
            logger.info("WebDriver quit.")
    except Exception:
        logger.exception("Error quitting WebDriver (ignored)")


if __name__ == "__main__":
    main()
