import time

import win32api
import win32print

from src.core.exceptions import HardwareError
from src.utils.logger import logger


class NativePDFStrategy:
    """
    Strategy to print PDF documents by using Windows default viewer
    """
    
    def execute_print(self, file_path: str, printer_name: str) -> bool:
        """
        Executes document print using the windows native approach

        Args:
            file_path (str): File path of the document to print
            printer_name (str): Target device to use for printing

        Returns:
            bool: True if print successful False if not
        """
        old_printer = None
        try:
            old_printer = win32print.GetDefaultPrinter()
            win32print.SetDefaultPrinter(printer_name)
            
            win32api.ShellExecute(0, "print", file_path, None, ".", 0)
            
            time.sleep(0.2)
            
            return True
        
        except Exception as e:
            logger.exception("Fail on the native subsystem while processing PDF")
            raise HardwareError(
                f"The OS could not print the PDF, verify that you have "
                f"a default lector (e.g. Edge, Acrobat) set: {str(e)}"
            ) from e
            
        finally:
            if old_printer:
                try:
                    win32print.SetDefaultPrinter(old_printer)
                except Exception:
                    logger.warning("It couldnt restore default printer")