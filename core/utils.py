import time
import logging
from functools import wraps

# 配置全局日志格式
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def rate_limit(seconds: float):
    """
    调用前强制 sleep 指定秒数，用于限速。
    用法：
        @rate_limit(1.0)
        def fetch(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Rate limiting: sleeping {seconds} seconds")
            time.sleep(seconds)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry(times: int = 3, exceptions: tuple = (Exception,)):
    """
    出错时自动重试。
    用法：
        @retry(times=5, exceptions=(ValueError, IOError))
        def fetch(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logger.warning(f"Attempt {attempt}/{times} failed: {e}")
            logger.error(f"All {times} attempts failed.")
            raise last_exc
        return wrapper
    return decorator
