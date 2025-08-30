# core/crawler.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import os
from .utils import logger, ensure_parent_dir


class BaseCrawler(ABC):
    """
    Generic crawler base class.
    Subclasses must implement: fetch_list, parse_list, fetch_detail, parse_detail.
    The crawler collects detail records into `self.results` (a list of dicts).
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.results: List[Dict[str, Any]] = []

    @abstractmethod
    def fetch_list(self) -> List[str]:
        """
        Fetch list pages and return a list of raw HTML strings (or list-response objects).
        """
        raise NotImplementedError

    @abstractmethod
    def parse_list(self, html_list) -> List[str]:
        """
        Parse list pages and return a list of identifiers or URLs for detail pages.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_detail(self, item) -> str:
        """
        Fetch a single detail page and return its HTML as a string.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_detail(self, html_detail: str) -> Dict[str, Any]:
        """
        Parse detail page HTML and return a dictionary of fields.
        """
        raise NotImplementedError

    def save(self, output_path: Optional[str]) -> None:
        """
        Persist results (list[dict]) to CSV or Excel based on file extension.
        If output_path is None or empty, raises ValueError.
        """
        if not output_path:
            raise ValueError("output_path is required for saving results.")

        if not self.results:
            logger.warning("No data to save.")
            # Still create parent dir so debug pages can be written consistently
            ensure_parent_dir(output_path)
            return

        df = pd.DataFrame(self.results)
        ensure_parent_dir(output_path)
        ext = os.path.splitext(output_path)[1].lower().lstrip('.')

        if ext == 'csv' or ext == '':
            df.to_csv(output_path, index=False, encoding='utf-8')
        elif ext in ('xls', 'xlsx'):
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {ext}")

        logger.info(f"Saved {len(self.results)} records to {output_path}")
