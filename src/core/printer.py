import os
import sys
import time

if sys.platform == "win32":
    from win32 import win32print


def _monitor_print_job(printer_name: str, job_id: int) -> None:
    """
    Monitors a specific Windows print job until it completes or fails

    Args:
        printer_name (str): The target system printer name
        job_id (int): The unique identifier of the submitted print job

    Raises:
        RuntimeError: If the print job encounters a hardware or driver error
    """

    hprinter = win32print.Open(printer_name)

    try:
        while True:
            try:
                job_info = win32print.GetJob(hprinter, job_id, 1)
            except Exception:
                break

            status = job_info.get("Status", 0)

            if status & win32print.JOB_STATUS_ERROR:
                raise RuntimeError(
                    f"La impresora reportó un error crítico de hardware")
            if status & win32print.JOB_STATUS_PAPEROUT:
                raise RuntimeError(
                    f"La impresora se ha quedado sin papel")
            if status & win32print.JOB_STATUS_OFFLINE:
                raise RuntimeError(
                    f"La impresora cambió a estado fuera de línea")

            if status & win32print.JOB_STATUS_PRINTED:
                break

            time.sleep(0.5)

    finally:
        win32print.ClosePrinter(hprinter)


def send_to_system_printer(file_path: str, watch_status: bool) -> None:
    """
    Sends a processed file directly to the OS default print spooler

    Args:
        file_path (str): The absolute or relative to the file to be printed
        watch_status (bool): If True, blocks execution until the job finishes printing

    Raises:
        FileNotFoundError: If the specified file does not exists
        RunTimeError: If the print platform is unsupported or the OS operation fails.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"The file to print was not found at {file_path}")

    if sys.platform == "win32":
        try:
            default_printer = win32print.GetDefaultPrinter()
            
            hprinter = win32print.OpenPrinter(default_printer)
            
            try:
                os.startfile(filepath=file_path, operation="print")
                time.sleep(1.0)
                
                if watch_status:
                    jobs = win32print.EnumJobs(hprinter, 0, 100, 1)
                    if jobs:
                        latest_job_id = jobs[-1]["JobId"]
                        _monitor_print_job(printer_name=default_printer, job_id=latest_job_id)
            finally:
                win32print.ClosePrinter(hprinter)
            
        except Exception as e:
            raise RuntimeError(
                f"Windows native print sub-system failed: {e}")
    else:
        raise RuntimeError(
            f"Unsupported operating system: {sys.platform}"
            f"Direct hardware printing is currently optimized for Windows"
        )
