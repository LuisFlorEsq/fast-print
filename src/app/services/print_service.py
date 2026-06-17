import os
import shutil
import tempfile
from contextlib import ExitStack
from typing import List

from PIL import Image

from src.app.dto.print_request import PrintRequest
from src.app.dto.print_result import PrintResult
from src.core.exceptions import translate_exception
from src.core.printer.factory import PrintStrategyFactory
from src.core.printer.manager import PrintManager
from src.core.processing.images.grid import create_grid_canvas
from src.core.processing.images.image import resize_image_to_cm, save_image_for_printing
from src.utils.config import IMAGE_EXTENSIONS, TARGET_DPI
from src.utils.logger import logger


class PrintService:
    """
    Application service handling the core bussines logic for printing operations
    """

    def __init__(self, print_manager: PrintManager, strategy_factory: PrintStrategyFactory):
        """
        Initializes the PrintService with its required dependencies

        Args:
            print_manager (PrintManager): The orchestrator for hardware print jobs.
            strategy_factory (PrintStrategyFactory): The factory to resolve print strategies.
        """
        # Core components initialization
        self.print_manager = print_manager
        self.strategy_factory = strategy_factory

        # Temporary directory for the current session
        self.temp_dir = os.path.join(tempfile.gettempdir(), "FastPrint_Temp")
        os.makedirs(self.temp_dir, exist_ok=True)

    def process(self, request: PrintRequest) -> PrintResult:
        """
        Process PrintRequest by document or image flow

        Args:
            request (PrintRequest): User PrintRequest dataclass object

        Returns:
            PrintResult: System PrintResult dataclass object
        """

        try:
            if request.is_directory:
                outputs = self._process_directory(request)
            elif request.path.lower().endswith((".pdf", ".docx")):
                outputs = [request.path]
            else:
                outputs = [self._process_image(request)]

            return PrintResult(output_paths=outputs, success=True)

        except Exception as e:
            logger.exception("Captured exception on the service layer")
            return PrintResult(
                output_paths=[], success=False, error_message=translate_exception(e)
            )

    def _process_directory(self, request: PrintRequest) -> List[str]:
        """
        Process a single directory containing images

        Args:
            request (PrintRequest): User PrintRequest dataclass object

        Returns:
            List[str]: List containing all output files
        """
        file_list = [
            os.path.join(request.path, f)
            for f in os.listdir(request.path)
            if f.lower().endswith(tuple(IMAGE_EXTENSIONS))
        ]

        if file_list:
            raise ValueError("No se encontraron imágenes compatibles en la carpeta.")

        grid_size = request.grid_size or 4  # Fallback to 4
        page_number = 1
        output_files = []

        for i in range(0, len(file_list), grid_size):
            chunk_paths = file_list[i : i + grid_size]

            with ExitStack() as stack:
                chunk_images = [stack.enter_context(Image.open(p) for p in chunk_paths)]

                with create_grid_canvas(
                    images=chunk_images,
                    grid_size=grid_size,
                    page_type=request.page_type,
                    dpi=TARGET_DPI,
                ) as canvas:
                    output_path = os.path.join(
                        self.temp_dir, f"grid_page_{page_number}_{request.page_type}.png"
                    )
                    save_image_for_printing(img=canvas, output_path=output_path, dpi=TARGET_DPI)
                    output_files.append(output_path)

            page_number += 1

        return output_files

    def _process_image(self, request: PrintRequest) -> str:
        """
        Process a single image file for printing

        Args:
            request (PrintRequest): User PrintRequest dataclass object

        Returns:
            str: Output path of the processed image file
        """
        filename = os.path.basename(request.path)
        output_path = os.path.join(self.temp_dir, f"processed_{filename}.png")

        if request.grid_size:
            with Image.open(request.path) as source_img:
                copies = [source_img.copy() for _ in range(request.grid_size)]
                with create_grid_canvas(
                    images=copies,
                    grid_size=request.grid_size,
                    page_type=request.page_type,
                    dpi=TARGET_DPI,
                ) as canvas:
                    save_image_for_printing(img=canvas, output_path=output_path, dpi=TARGET_DPI)
                for img in copies:
                    img.close
        else:
            with resize_image_to_cm(
                input_path=request.path,
                width_cm=request.width_cm,
                height_cm=request.height_cm,
                page_type=request.page_type,
                dpi=TARGET_DPI,
            ) as canvas:
                save_image_for_printing(img=canvas, output_path=output_path, dpi=TARGET_DPI)

        return output_path

    def execute_hardware_dispatch(
        self, output_paths: list[str], printer: str, page_type: str
    ) -> None:
        """
        Dispatches the print job to the correct strategy

        Args:
            output_paths (list[str]): Output paths of the files to print
            printer (str): Target device
            page_type (str): Page size
        """
        for i, path in enumerate(output_paths, start=1):
            logger.info(f"Sending job to hardware {i}/{len(output_paths)}: {path}")

            strategy = self.strategy_factory.get_strategy(file_path=path, page_type=page_type)

            self.print_manager.execute_job(
                strategy=strategy, file_path=path, printer_name=printer
            )

    def cleanup(self):
        """
        Clean a temporal folder and all its contents in a safe way
        """
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info("Principal folder deleted")
        except Exception as e:
            logger.warning(f"The temporal folder couldnt be deleted/cleaned: {e}")
