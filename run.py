import argparse
import yaml
import importlib
from core.crawler import BaseCrawler

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Run web crawler with given config")
    parser.add_argument('--config', '-c', required=True, help="Path to YAML config file")
    args = parser.parse_args()

    config = load_config(args.config)
    # 假设 config.yaml 中指定了 crawler_class，格式为: module.ClassName
    module_name, class_name = config['crawler_class'].rsplit('.', 1)
    module = importlib.import_module(module_name)
    crawler_cls = getattr(module, class_name)
    if not issubclass(crawler_cls, BaseCrawler):
        raise TypeError(f"{crawler_cls} is not a subclass of BaseCrawler")

    crawler = crawler_cls(config)
    html_list = crawler.fetch_list()
    print(f"⚙️ Fetched HTML pages: {len(html_list)}")   # ← 新增

    items = crawler.parse_list(html_list)
    print(f"⚙️ Parsed items: {items}")                  # ← 新增

    for item in items:
        html_detail = crawler.fetch_detail(item)
        record = crawler.parse_detail(html_detail)
        crawler.results.append(record)

    output = config.get('output_path', f"{config['site_name']}.csv")
    crawler.save(output)

if __name__ == '__main__':
    main()
