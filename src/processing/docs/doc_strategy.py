import os
import time
import subprocess

from abc import ABC, abstractmethod
from typing import Optional

from src.utils.logger import logger

try:
    import win32com.client
    import pythoncom
    import win32print
except ImportError:
    win32com = None
    

class DocumentPrintStrategy(ABC):
    """
    Abstract base class defining the interface for document printing strategies
    """
    
    @abstractmethod
    def execute_print(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Executes the print operation

        Args:
            file_path (str): The absolute path to the document
            printer_name (Optional[str], optional): The target printer. Defaults to None.

        Returns:
            bool: True if the print job was successfully dispatched, False otherwise
        """
        
        

class WordComStrategy(DocumentPrintStrategy):
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
        
        except Exception as e:

            logger.exception("COM automation failed")
            raise RuntimeError(
                "Fallo al procesar el documento con Microsoft Word."
                "Es posible que el archivo esté corrupto o bloqueado."
            )
            
        finally:
            if word_app:
                word_app.Quit()
            pythoncom.CoUninitialize()
            
            
class LibreOfficeStrategy(DocumentPrintStrategy):
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
            f"C:\Program Files\LibreOffice\program\soffice.exe",
            f"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return None
    
    def execute_print(self, file_path:str, printer_name: Optional[str] = None) -> bool:
        """
        Dispatches the document using the LibreOffice command line interface.

        Args:
            file_path (str): The absolute path to the document.
            printer_name (str, optional): The target printer. Defaults to None.

        Returns:
            bool: True if LibreOffice executed successfully, False if it is not installed.
            
        Raises:
            RuntimeError: If the subprocess fails to execute.
        """
        if not self.soffice_path:
            return False

        try:
            target_printer = printer_name if printer_name else win32print.GetDefaultPrinter()
            
            command = [
                self.soffice_path,
                "--headless",
                "--invisible",
                "--nodefault",
                "--nofirststartwizard",
                "-pt",
                target_printer,
                file_path
            ]
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(command, check=True, startupinfo=startupinfo)
            return True

        except subprocess.CalledProcessError:
            raise RuntimeError(
                "LibreOffice intentó imprimir el documento pero falló inesperadamente."
            )
            

def print_document_smart(file_path: str, printer_name: Optional[str] = None) -> None:
    """
    Context manager that attempts to print a document using the best availale strategy

    Args:
        file_path (str): Path to the target document
        printer_name (Optional[str], optional): Target hardware printer. Defaults to None.
    """
    
    word_strategy = WordComStrategy()
    if word_strategy.execute_print(file_path=file_path, printer_name=printer_name):
        return
    
    libre_strategy = LibreOfficeStrategy()
    if libre_strategy.execute_print(file_path=file_path, printer_name=printer_name):
        return
    
    raise RuntimeError(
        "No se puede imprimir el documento. Instala Microsoft Word o LibreOffice para habilitar esta funcion"
    )