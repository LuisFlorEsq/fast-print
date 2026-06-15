from enum import IntEnum


class PaperSize(IntEnum):
    """
    Standard paper size for windows API
    """
    LETTER = 1
    A4 = 9
    
class DeviceCaps(IntEnum):
    """
    Hardware limitations for win32ui
    """
    HResolution = 8
    VResolution = 10
    

DEFAULT_QUEUE_TIMEOUT = 120
INITIAL_POLL_INTERVAL = 0.25
MAX_POLL_INTERVAL = 2.0