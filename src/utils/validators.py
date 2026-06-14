import zipfile
from pathlib import Path

from PIL import Image

from src.core.exceptions import ValidationError
from src.utils.config import PAGE_SIZES

# --------------------------------------------
# Baseline Validations
# ---------------------------------------------


def validate_page_type(page_type: str) -> None:
    """
    Check if the input page type corresponds to a availbale page size [letter, A4]

    Args:
        page_type (str): User requested page size
    """

    if page_type.lower() not in PAGE_SIZES:
        raise ValidationError(f"Unsupported page_type: {page_type}")


def validate_dimensions(width_cm: float, height_cm: float) -> None:
    """
    Check if user input dimensions are valid

    Args:
        width_cm (float): Target width on image resizing
        height_cm (float): Target height on image resizing
    """

    if width_cm is None and height_cm is None:
        raise ValidationError("You must specify width or height")

    if width_cm is not None and width_cm < 0:
        raise ValidationError("Width must be greater than 0 cm")

    if height_cm is not None and height_cm < 0:
        raise ValidationError("Height must be greater than 0 cm")


def validate_path(path: str) -> None:
    """
    Check if a given path exists

    Args:
        path (str): User input path
    """

    if not path:
        raise ValidationError("Path cannot be empty.")

    if not Path(path).exists():
        raise ValidationError(f"Path does not exist: {path}")


def validate_printer(printer_name: str, available_printers: list[str]) -> None:
    """
    Checks that the target printer exists on system available printers

    Args:
        printer_name (str): Target device
        available_printers (list[str]): System available printers
    """

    if not printer_name:
        return

    if printer_name not in available_printers:
        raise ValidationError(f"Invalid printer selected: {printer_name}")


# --------------------------------------------
# File integrity validation
# ---------------------------------------------


def validate_image_file(path: str) -> None:
    """
    Checks if the input path contains an image file

    Args:
        path (str): Image input path
    """
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as e:
        raise ValidationError(f"Invalid or corrupted image file: {path}") from e


def validate_pdf_file(path: str) -> None:
    """
    Checks if the inputh path contains a .pdf file

    Args:
        path (str): Pdf input path
    """
    try:
        with open(path, "rb") as f:
            header = f.read(4)

            if header != b"%PDF":
                raise ValidationError("Invalid PDF file")

    except Exception as e:
        raise ValidationError(f"Corrupted PDF file: {path}") from e


def validate_docx_file(path: str) -> None:
    """
    Checks if the input path contains a .docx file

    Args:
        path (str): Docx input path
    """
    try:
        with zipfile.ZipFile(path, "r") as archive:
            if "[Content_Types].xml" not in archive.namelist():
                raise ValidationError("Invalid DOCX file.")

    except Exception as e:
        raise ValidationError(f"Corrupted DOCX file: {path}") from e


# --------------------------------------------
# Dimensions bounds validation
# ---------------------------------------------


def validate_image_fits(
    width_cm: float | None, height_cm: float | None, page_type: str
) -> None:
    """
    Checks if the user input dimensions for resizing an image fits on the selected page

    Args:
        width_cm (float | None): User target width for image
        height_cm (float | None): User target height for image
        page_type (str): User requested page type (letter, A4)
    """

    page_w, page_h = PAGE_SIZES[page_type.lower()]

    margin_cm = 4.0
    max_w = page_w - margin_cm
    max_h = page_h - margin_cm

    if width_cm and width_cm > max_w:
        raise ValidationError(f"Image width exceeds printable area ({max_w:.1f} cm)")

    if height_cm and height_cm > max_h:
        raise ValidationError(f"Image height exceeds printable area ({max_h:.1f} cm)")
