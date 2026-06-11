import os
import sys
import time
from typing import List, Optional
from PIL import Image, ImageWin

if sys.platform == "win32":
    import win32print
    import win32ui
    import win32api


class PrintManager:
    """
    Singleton manager that controls access to the Windows print spooler

    Ensures that hardware requests are queued and processed sequentially
    to prevent resource exhaustion and spooler crashes
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        # Enforce Singleton pattern by creating the instance only once
        if not cls._instance:
            cls._instance = super(PrintManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization of variables if the instance already exists
        if not self._initialized:
            self._initialized = True

    def get_available_printers(self) -> List[str]:
        """
        Retrieves a list of all printer names configured on the Windows System

        Returns:
            List[str]: A list of strings containing local and network printer names
            Returns an empty list if not running on Windows platform
        """

        if sys.platform != "win32":
            return []

        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printer_tuples = win32print.EnumPrinters(flags, None, 1)

        return [printer[2] for printer in printer_tuples]

    def send_to_printer(self, file_path: str, printer_name: Optional[str] = None, page_type: str = "letter") -> None:
        """
        Dispatches a file to the specified Windows print spooler safely

        Args:
            file_path (str): The absolute path to the file to be printed
            printer_name (Optional[str], optional): The name of the specific printer device. Defaults to None.
            page_type (str, optional): The page size to format. Defaults to "letter".
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                F"No se pudo encontrar el archivo en la ruta: {file_path}")

        if sys.platform != "win32":
            raise RuntimeError(
                "La impresion directa solo esta optimizada para sistemas Windows")

        target_device = printer_name if printer_name else win32print.GetDefaultPrinter()

        if file_path.lower().endswith('.pdf'):
            self._print_pdf(file_path, target_device)

        else:
            self._print_image(file_path, target_device, page_type)

    def _print_pdf(self, file_path: str, printer_name: str) -> None:
        """
        Sends a PDF file to the printer  using Windows ShellExecute API

        Args:
            file_path (str): Absolute path to the PDF file
            printer_name (str): Target printer device name
        """
        try:
            win32api.ShellExecute(
                0,
                "printto",
                file_path,
                f'"{printer_name}"',
                ".",
                0
            )
            time.sleep(2.0)
        except Exception as e:
            raise RuntimeError(
                f"Fallo al enviar el archivo PDF al spooler de impresión: {str(e)}")

    def _print_image(self, file_path: str, printer_name: str, page_type: str) -> None:
        """
        Sends an image file directly to the printer graphics context with active monitoring.

        Args:
            file_path (str): Absolute path to the image file.
            printer_name (str): Target printer device name.
            page_type (str): Target page size ("letter" or "a4").

        Raises:
            RuntimeError: If the hardware context cannot be opened or fails during transmission.
        """
        hprinter = None
        hdc = None

        try:
            hprinter = win32print.OpenPrinter(printer_name)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)

            paper_code = 1 if page_type.lower() == "letter" else 9

            try:
                devmode = win32print.GetPrinter(hprinter, 2)["pDevMode"]
                devmode.PaperSize = paper_code
                hdc.ResetDC(devmode)
            except Exception:
                pass

            doc_name = f"FastPrint_{os.path.basename(file_path)}"
            hdc.StartDoc(doc_name)
            hdc.StartPage()

            # Retrieve printable area dimensions
            printer_width = hdc.GetDeviceCaps(8)
            printer_height = hdc.GetDeviceCaps(10)

            with Image.open(file_path) as img:
                img_aspect = img.width / img.height
                page_aspect = printer_width / printer_height

                # Calculate dimensions to maintain aspect ratio
                if img_aspect > page_aspect:
                    draw_w = printer_width
                    draw_h = int(printer_width / img_aspect)
                else:
                    draw_h = printer_height
                    draw_w = int(printer_height * img_aspect)

                # Center the image on the page
                x_offset = (printer_width - draw_w) // 2
                y_offset = (printer_height - draw_h) // 2

                # Convert image to Windows Device Independent Bitmap (DIB) and draw
                dib = ImageWin.Dib(img)
                dib.draw(hdc.GetSafeHdc(), (x_offset, y_offset,
                                            x_offset + draw_w, y_offset + draw_h))

            # Finish the page and document processing
            hdc.EndPage()
            hdc.EndDoc()

        except Exception as e:
            raise RuntimeError(
                f"Error de hardware al procesar la imagen: {str(e)}")

        finally:
            if hdc:
                try:
                    hdc.DeleteDC()
                except Exception:
                    pass

            if hprinter:
                win32print.ClosePrinter(hprinter)

        # Trigger active queue monitoring right after sending data and releasing hardware locks
        self._monitor_device_queue(printer_name)


    def _monitor_device_queue(self, printer_name: str, timeout_seconds: int = 30) -> None:
        """
        Monitors the active printer queue until all current jobs clear or fail

        Args:
            printer_name (str): Target printer to monitor
            timeout_seconds (int): Maximum time to wait for the queue to clear. Defaults to 30
        """
        hprinter = win32print.OpenPrinter(printer_name)
        start_time = time.time()

        try:
            while True:

                if time.time() - start_time > timeout_seconds:
                    raise TimeoutError(
                        f"Tiempo de espera agotado ({timeout_seconds}s). "
                        "El trabajo sigue en la cola de Windows. Verifica la conexión de tu impresora."
                    )

                printer_info = win32print.GetPrinter(hprinter, 2)
                job_count = printer_info.get("cJobs", 0)

                if job_count == 0:
                    break

                jobs = win32print.EnumJobs(hprinter, 0, -1, 2)

                if jobs:
                    status = jobs[0].get("Status", 0)
                    if status & win32print.JOB_STATUS_ERROR:
                        raise RuntimeError(
                            "La impresora reportó un error crítico de hardware.")
                    elif status & win32print.JOB_STATUS_PAPEROUT:
                        raise RuntimeError(
                            "La impresora se ha quedado sin papel o está atascada.")
                    elif status & win32print.JOB_STATUS_OFFLINE:
                        raise RuntimeError(
                            "La impresora cambió a estado fuera de línea.")

                time.sleep(0.5)
        finally:
            win32print.ClosePrinter(hprinter)
