import os

from src.core.printer.strategies.base_strategy import PrintStrategy
from src.core.printer.strategies.doc_strategy import DocumentPrintStrategy
from src.core.printer.strategies.image_strategy import ImagePrintStrategy
from src.core.printer.strategies.pdf_strategy import PDFPrintStrategy
from src.utils.config import IMAGE_EXTENSIONS


class PrintStrategyFactory:
    """
    Static factory for dynamically instantiating print strategies.
    """

    @staticmethod
    def get_strategy(file_path: str, page_type: str = "letter") -> PrintStrategy:
        """
        Return the corresponding Print strategy based on the file extension

        Args:
            file_path (str): Absolute path of the file to print
            page_type (str, optional): Page size. Defaults to "letter".

        Returns:
            PrintStrategy: Corresponding Print Strategy for the file requested to print
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return PDFPrintStrategy()
        if ext == ".docx":
            return DocumentPrintStrategy()
        if ext in IMAGE_EXTENSIONS:
            return ImagePrintStrategy()

        raise ValueError(f"File format not supported: {ext}")
