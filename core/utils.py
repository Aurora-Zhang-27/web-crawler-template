# core/utils.py
import time
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type

# Basic logger configuration used across the project
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("webcrawler")

def ensure_parent_dir(path: str) -> None:
    """
    Create parent directory for a given path if it does not exist.
    Works for files (creates dirname) and for directories (if path ends with '/').
    """
    if not path:
        return
    parent = None
    if path.endswith('/') or path.endswith('\\'):
        parent = path
    else:
        parent = __import__('os').path.dirname(path)
    if parent:
        __import__('os').makedirs(parent, exist_ok=True)

def rate_limit(seconds: float):
    """
    Decorator to sleep for `seconds` before calling the function.
    Useful to throttle requests.
    """
    def deco(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if seconds and seconds > 0:
                logger.debug(f"Rate limit: sleeping {seconds} seconds")
                time.sleep(seconds)
            return func(*args, **kwargs)
        return wrapper
    return deco


def retry(times: int = 3, exceptions: Tuple[Type[BaseException], ...] = (Exception,)):
    """
    Simple retry decorator. Retries the wrapped function up to `times` when one of the
    specified exceptions is raised. After final failure, re-raises the last exception.
    """
    def deco(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logger.warning(f"Attempt {attempt}/{times} failed: {e}")
            logger.error(f"All {times} attempts failed for function {func.__name__}")
            raise last_exc
        return wrapper
    return deco
