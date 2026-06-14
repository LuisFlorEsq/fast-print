from dataclasses import dataclass
from typing import Optional


@dataclass
class PrintRequest:
    path: str
    printer: Optional[str]
    page_type: str
    width_cm: Optional[float]
    height_cm: Optional[float]
    grid_size: Optional[int]
    is_directory: bool
    print_now: bool
