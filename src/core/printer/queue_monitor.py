import time
import win32print
from src.core.exceptions import HardwareError, QueueTimeoutError
from src.utils.logger import logger

from src.core.printer.constants import INITIAL_POLL_INTERVAL, MAX_POLL_INTERVAL


class PrintQueueMonitor:
    def __init__(self, timeout_seconds: int = 45):
        self.timeout_seconds = timeout_seconds

    def wait_job_completion(self, printer_name: str) -> None:
        """
        Check for print job completion avoiding to wait undefined

        Args:
            printer_name (str): Target device to monitor

        Raises:
            QueueTimeoutError: Error when the wait time was reached
        """
        logger.info(f"Monitoring printer queue: {printer_name}")
        hprinter = win32print.OpenPrinter(printer_name)
        start_time = time.time()

        poll_interval = INITIAL_POLL_INTERVAL
        max_interval = MAX_POLL_INTERVAL

        try:
            while True:
                if time.time() - start_time > self.timeout_seconds:
                    raise QueueTimeoutError(f"Tiempo de espera agotado ({self.timeout_seconds}s)")

                printer_info = win32print.GetPrinter(hprinter, 2)
                if printer_info.get("cJobs", 0) == 0:
                    logger.info("Jobs correctly dispatched")
                    break

                jobs = win32print.EnumJobs(hprinter, 0, -1, 2)
                if jobs:
                    status = jobs[0].get("Status", 0)
                    if status & win32print.JOB_STATUS_ERROR:
                        raise HardwareError("Critical Hardware error reported")
                    elif status & win32print.JOB_STATUS_PAPEROUT:
                        raise HardwareError("Printer does not have paper or it is stuck")

                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, max_interval)

        finally:
            win32print.ClosePrinter(hprinter)
