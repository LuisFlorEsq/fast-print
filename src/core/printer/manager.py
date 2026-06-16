import sys

import win32print

from src.core.printer.queue_monitor import PrintQueueMonitor
from src.core.printer.strategies.base_strategy import PrintStrategy
from src.utils.logger import logger


class PrintManager:
    """
    Routing orchestator for the Windows spooler
    """

    def __init__(self, queue_monitor: PrintQueueMonitor = None):
        self.queue_monitor = queue_monitor or PrintQueueMonitor()  # Init queue monitor service

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

    def execute_job(self, strategy: PrintStrategy, file_path: str, printer_name: str) -> None:
        """
        Recieves a specific strategy and executes it

        Args:
            strategy (PrintStrategy): Specific PrintStrategy (Image, Doc, Pdf)
            file_path (str): Document filepath
            printer_name (str): Target device
        """

        target_device = printer_name or win32print.GetDefaultPrinter()
        logger.info(f"Executing print job in: {target_device}")

        strategy.execute_print(file_path=file_path, printer_name=target_device)

        self.queue_monitor.wait_job_completion(printer_name=target_device)
