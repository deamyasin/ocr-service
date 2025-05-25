"""OCR Service Package"""

from . import config
from . import processors
from . import task_queue

__all__ = ['config', 'processors', 'task_queue'] 