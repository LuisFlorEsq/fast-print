import os
import sys
import time
from typing import List
from PIL import Image, ImageWin

if sys.platform == "win32":
    from win32 import win32print
    import win32ui


def get_available_printers() -> List[str]:
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


def _monitor_device_queue(printer_name: str, timeout_seconds: int = 30) -> None:
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

            jobs = win32print.EnumJobs(hprinter, 0, 100, 1)

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


def print_image_directly(file_path: str, printer_name: str, page_type: str = "letter") -> None:
    """
    Sends an image file directly to the printer graphics context with active monitoring.

    Args:
        file_path (str): Target filepath to print
        printer_name (str): Target printer to use
        page_type (str, optional): Page size/dimensions. Defaults to "letter".
    """
    img = Image.open(file_path)

    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)

    paper_code = 1 if page_type.lower() == "letter" else 9

    try:
        devmode = win32print.GetPrinter(
            win32print.OpenPrinter(printer_name), 2)["pDevMode"]
        devmode.PaperSize = paper_code
        hdc.ResetDC(devmode)
    except Exception:
        pass

    doc_name = f"FastPrint_{os.path.basename(file_path)}"
    hdc.StartDoc(doc_name)
    hdc.StartPage()

    printer_width = hdc.GetDeviceCaps(8)
    printer_height = hdc.GetDeviceCaps(10)

    img_aspect = img.width / img.height
    page_aspect = printer_width / printer_height

    if img_aspect > page_aspect:
        draw_w = printer_width
        draw_h = int(printer_width / img_aspect)
    else:
        draw_h = printer_height
        draw_w = int(printer_height * img_aspect)

    x_offset = (printer_width - draw_w) // 2
    y_offset = (printer_height - draw_h) // 2

    dib = ImageWin.Dib(img)
    dib.draw(hdc.GetSafeHdc(), (x_offset, y_offset,
             x_offset + draw_w, y_offset + draw_h))

    hdc.EndPage()
    hdc.EndDoc()
    hdc.DeleteDC()
    img.close()

    # Trigger active queue monitoring right after sending data
    _monitor_device_queue(printer_name)


def send_to_system_printer(file_path: str, printer_name: str = None, page_type: str = "letter") -> None:
    """
    Sends a processed file directly to a specified of default Windows print spooler

    Args:
        file_path (str): The absolute or relative to the file to be printed
        printer_name (str): The name of the specific printer device

    Raises:
        FileNotFoundError: If the specified file does not exists
        ValueError: If the specified printer name does not exists on the system.
        RunTimeError: If the print platform is unsupported or the OS operation fails.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"The file to print was not found at {file_path}")

    if sys.platform != "win32":
        raise RuntimeError(
            "Direct hardware printing tracking is only optimized for Windows")

    target_device = printer_name if printer_name else win32print.GetDefaultPrinter()

    if file_path.lower().endswith('.pdf'):
        original_default = win32print.GetDefaultPrinter()
        try:
            if target_device != original_default:
                win32print.SetDefaultPrinter(target_device)
            os.startfile(filepath=file_path, operation="print")
            time.sleep(1.5)
            _monitor_device_queue(target_device)

        finally:
            if target_device != original_default:
                win32print.SetDefaultPrinter(original_default)

    else:
        print_image_directly(file_path=file_path,
                             printer_name=printer_name, page_type=page_type)
