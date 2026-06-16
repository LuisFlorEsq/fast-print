from abc import ABC, abstractmethod


class PrintStrategy(ABC):
    """
    Base interface for all print strategies
    """

    @abstractmethod
    def execute_print(self, file_path: str, printer_name: str) -> bool:
        """
        Executes specific printer operation

        Args:
            file_path (str): Target file's path
            printer_name (str): Target device

        Returns:
            bool: True if correctly printed, False if not
        """
        pass
