import os

import win32print
import win32ui
from PIL import Image, ImageWin

from core.printer.strategies.base_strategy import PrintStrategy
from src.core.exceptions import HardwareError
from src.core.printer.constants import DeviceCaps, PaperSize
from src.utils.logger import logger


class ImagePrintStrategy(PrintStrategy):
    """
    Strategy for printing images

    Args:
        PrintStrategy (_type_): _description_
    """

    def __init__(self, page_type: str = "letter"):
        self.page_type = page_type

    def execute_print(self, file_path: str, printer_name: str) -> bool:
        """
        Main flow to print an image file

        Args:
            file_path (str): Image filepath
            printer_name (str): Target device

        Returns:
            bool: True if jobs was correctly dispatched, False if not
        """

        hprinter = None
        hdc = None

        try:
            hprinter = win32print.OpenPrinter(printer_name)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)

            paper_code = PaperSize.LETTER if self.page_type.lower() == "letter" else PaperSize.A4

            try:
                devmode = win32print.GetPrinter(hprinter, 2)["pDevMode"]
                devmode.PaperSize = paper_code.value
                hdc.ResetDC(devmode)
            except Exception:
                logger.warning("Fallo al forzar configuración de página en GDI.")

            hdc.StartDoc(f"FastPrint_Img_{os.path.basename(file_path)}")
            hdc.StartPage()

            printer_w = hdc.GetDeviceCaps(DeviceCaps.HORZRES.value)
            printer_h = hdc.GetDeviceCaps(DeviceCaps.VERTRES.value)

            with Image.open(file_path) as img:
                dib = ImageWin.Dib(img)
                dib.draw(hdc.GetSafeHdc(), (0, 0, printer_w, printer_h))

            hdc.EndPage()
            hdc.EndDoc()
            return True

        except Exception as e:
            raise HardwareError(f"Error procesando el mapa de bits: {str(e)}")
        finally:
            if hdc:
                try:
                    hdc.DeleteDC()
                except Exception as e:
                    logger.warning(f"Unexpected error: {str(e)}")
            if hprinter:
                win32print.ClosePrinter(hprinter)
