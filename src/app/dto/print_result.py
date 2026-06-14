from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PrintResult:
    output_paths: List[str]
    success: bool
    error_message: Optional[str] = None
