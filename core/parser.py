from bs4 import BeautifulSoup

def extract_fields(html: str, selectors: dict) -> dict:
    """
    通用字段提取：
      - html: 页面源码
      - selectors: {字段名: CSS selector 或 (selector, attr) 元组}
    返回一个 dict，每个字段对应提取到的文本或属性值。
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    for field, rule in selectors.items():
        if isinstance(rule, (tuple, list)) and len(rule) == 2:
            sel, attr = rule
            elem = soup.select_one(sel)
            result[field] = elem.get(attr, "").strip() if elem else None
        else:
            elem = soup.select_one(rule)
            result[field] = elem.get_text(strip=True) if elem else None
    return result
