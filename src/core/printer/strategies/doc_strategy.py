import os
import subprocess
import time
from typing import Optional

from src.core.exceptions import DocumentProcessingError
from src.core.printer.strategies.base_strategy import PrintStrategy
from src.utils.logger import logger

try:
    import pythoncom
    import win32com.client
except ImportError:
    win32com = None


class WordComStrategy(PrintStrategy):
    """
    Strategy that uses Microsoft Word's COM interface to print invisibly
    """

    def execute_print(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Dispatches the document to the printer using background MS Word automation

        Args:
            file_path (str): The absolute path to the document
            printer_name (Optional[str], optional): The target printer. Defaults to None.

        Returns:
            bool: True if successful, False is MS Word is unavailable
        """
        if win32com is None:
            return False

        word_app = None

        try:
            pythoncom.CoInitialize()

            word_app = win32com.client.DispatchEx("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = False

            if printer_name:
                word_app.ActivePrinter = printer_name

            doc = word_app.Documents.Open(file_path, ReadOnly=True)

            doc.PrintOut(Background=False)
            time.sleep(1.0)

            doc.Close(SaveChanges=False)

            return True

        except Exception:
            logger.exception("COM automation failed")
            raise DocumentProcessingError(
                "Fallo al procesar el documento con Microsoft Word."
                "Es posible que el archivo esté corrupto o bloqueado."
            )

        finally:
            if word_app:
                word_app.Quit()
            pythoncom.CoUninitialize()


class LibreOfficeStrategy(PrintStrategy):
    """
    Fallback strategy that uses LibreOffice headless mode to print the document
    """

    def __init__(self):
        """
        Initialize the strategy by trying to locate the LibreOffixe executable
        """
        self.soffice_path = self._find_libreoffice()

    def _find_libreoffice(self) -> Optional[str]:
        """
        Scans common Windows installation directories for the LibreOffice executable

        Returns:
            Optional[str]: Path to the soffice.exe if found, None otherwise
        """
        common_paths = [
            "C:\Program Files\LibreOffice\program\soffice.exe",
            "C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return None

    def execute_print(self, file_path: str, printer_name: Optional[str]) -> bool:
        """
        Dispatches the document to the printer using background LibreOffice automation

        Args:
            file_path (str): The absolute path to the document
            printer_name (Optional[str], optional): The target printer. Defaults to None.

        Returns:
            bool: True if successful, False is MS Word is unavailable
        """

        if not self.soffice_path:
            return False  # LibreOffice not found

        try:
            command = [
                self.soffice_path,
                "--headless",
                "--invisible",
                "--nodefault",
                "--nofirststartwizard",
                "-pt",
                printer_name,
                file_path,
            ]

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(command, check=True, startupinfo=startupinfo)
            return True

        except subprocess.CalledProcessError as e:
            logger.warning(f"LibreOffice execution fails: {str(e)}")
            return False


class DocumentPrintStrategy(PrintStrategy):
    """
    Compound strategy which implements a robust fallback mechanism

    Args:
        PrintStrategy (_type_): _description_
    """

    def execute_print(self, file_path: str, printer_name: Optional[str]) -> bool:
        """
        Main print method for .docx files

        Args:
            file_path (str): Absolute path of the document to print
            printer_name (Optional[str]): Target device

        Returns:
            bool: True if job completed, False if not
        """
        logger.info("Executing DocumentPrint Strategy")

        # First try using Word
        word_strategy = WordComStrategy()

        try:
            if word_strategy.execute_print(file_path=file_path, printer_name=printer_name):
                logger.info("Document print completed using Microsoft Word")
                return True
        except Exception as e:
            logger.warning(f"Word Strategy failed: {e}, Trying LibreOffice fallback")

        # Fallback to LibreOffice
        libre_strategy = LibreOfficeStrategy()
        try:
            if libre_strategy.execute_print(file_path=file_path, printer_name=printer_name):
                logger.info("Document print completed using LibreOffice")
                return True
        except Exception as e:
            logger.warning(f"Libre Office Strategy failed: {e}")

        # Critical error
        raise DocumentProcessingError(
            "DOCX document could not be printed"
            "Try installing Microsoft Word or LibreOffice to use this function"
        )
