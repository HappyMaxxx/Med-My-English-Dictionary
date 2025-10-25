import time
import logging
from datetime import datetime
from functools import wraps


logger = logging.getLogger(__name__)

def time_logger(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = function(*args, **kwargs)
        now = datetime.now()
        formatted = now.strftime("[%d/%b/%Y %H:%M:%S]")
        logger.info(f"{formatted} Function {function.__name__} executed in {time.time() - start:.3f} seconds")
        return result
    return wrapper