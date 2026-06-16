import os
import sys

import win32print
import win32ui
from PIL import Image, ImageWin

from src.core.exceptions import HardwareError
from src.core.printer.constants import DeviceCaps, PaperSize
from src.core.printer.pdf_strategy import PDFStrategy
from src.core.printer.queue_monitor import PrintQueueMonitor
from src.utils.logger import logger


class PrintManager:
    """
    Routing orchestator for the Windows spooler
    """

    def __init__(self, queue_monitor: PrintQueueMonitor = None):
        self.queue_monitor = queue_monitor
        self.pdf_strategy = PDFStrategy

    def get_available_printers(self) -> list[str]:
        """
        Obtain all the available printers for the current system session

        Returns:
            list[str]: List with all found printers
        """
        if sys.platform != "win32":
            return []

        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS

        return [printer[2] for printer in win32print.EnumPrinters(flags, None, 1)]

    def send_to_printer(
        self, file_path: str, printer_name: str = None, page_type: str = "letter"
    ) -> None:
        """
        Send a file to the target printer

        Args:
            file_path (str): File target path
            printer_name (str, optional): Target printer to use. Defaults to None.
            page_type (str, optional): Paper size. Defaults to "letter".
        """
        target_device = printer_name or win32print.GetDefaultPrinter()
        logger.info(f"Despachando {file_path} a {target_device}")

        if file_path.lower().endswith(".pdf"):
            self.pdf_strategy.execute_print(file_path=file_path, printer_name=target_device)
        else:
            self._print_image()

    def _print_image(self, file_path: str, printer_name: str, page_type: str) -> None:
        """
        Main flow to send an image file to the printer

        Args:
            file_path (str): File target path
            printer_name (str): Targer printer to use
            page_type (str): Paper/Page size
        """

        hprinter = None
        hdc = None

        try:
            hprinter = win32print.OpenPrinter(printer_name)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)

            paper_code = PaperSize.LETTER if page_type.lower() == "letter" else PaperSize.A4

            try:
                devmode = win32print.GetPrinter(hprinter, 2)["pDevMode"]
                devmode.PaperSize = paper_code.value
                hdc.ResetDC(devmode)
            except Exception:
                logger.warning("Fail when trying to inject paper configuration")

            hdc.StartDoc(f"FastPrint_Img_{os.path.basename(file_path)}")
            hdc.StartPage()

            printer_w = hdc.GetDeviceCaps(DeviceCaps.WResolution.value)
            printer_h = hdc.GetDeviceCaps(DeviceCaps.HResolution.value)

            with Image.open(file_path) as img:
                dib = ImageWin.Dib(img)
                dib.draw(hdc.GetSafeHdc(), (0, 0, printer_w, printer_h))

            hdc.EndPage()
            hdc.EndDoc()

        except Exception as e:
            raise HardwareError(f"GDI error processing bit map: {str(e)}")

        finally:
            if hdc:
                try:
                    hdc.DeleteDC()
                except:
                    pass
            if hprinter:
                win32print.ClosePrinter(hprinter)

        self.queue_monitor.wait_job_completion(printer_name=printer_name)
