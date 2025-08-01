from abc import ABC, abstractmethod
import pandas as pd
from core.utils import logger

class BaseCrawler(ABC):
    """
    通用爬虫抽象基类。子类需实现 fetch_list/parse_list/fetch_detail/parse_detail。
    """
    def __init__(self, config: dict):
        self.config = config
        self.results = []

    @abstractmethod
    def fetch_list(self) -> list:
        """
        抓取列表页，返回原始响应或 HTML 列表。
        """
        pass

    @abstractmethod
    def parse_list(self, html_list) -> list:
        """
        解析列表页内容，抽取每条记录的标识或 URL，
        返回可用于 fetch_detail 的参数列表。
        """
        pass

    @abstractmethod
    def fetch_detail(self, item) -> str:
        """
        抓取单条记录详情页的 HTML 文本。
        """
        pass

    @abstractmethod
    def parse_detail(self, html_detail) -> dict:
        """
        解析详情页 HTML，返回字段字典，例如 {'title': ..., 'date': ..., ...}
        """
        pass

    def save(self, output_path: str):
        """
        将 self.results（列表[dict]）转换为 DataFrame 并写入文件。
        """
        if not self.results:
            logger.warning("No data to save.")
            return

        df = pd.DataFrame(self.results)
        ext = output_path.split(".")[-1].lower()
        if ext in ("csv",):
            df.to_csv(output_path, index=False)
        elif ext in ("xlsx", "xls"):
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {ext}")
        logger.info(f"Saved {len(self.results)} records to {output_path}")
