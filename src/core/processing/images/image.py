from PIL import Image

from src.core.exceptions import ImageProcessingError
from src.utils.config import INCH_PER_CM, PAGE_SIZES, TARGET_DPI


def cm_to_pixels(cm: float, dpi: int = TARGET_DPI) -> int:
    """
    Converts a size in centimeters to pixels based on the DPI

    Args:
        cm (float): User input size in cm
        dpi (int, optional): Dots Per Inch, pixels fit in one inch. Defaults to 300.

    Returns:
        int: Output pixels
    """

    return int((cm / INCH_PER_CM) * dpi)


def resize_image_to_cm(
    input_path: str,
    width_cm: float = None,
    height_cm: float = None,
    page_type: str = "letter",
    dpi: int = TARGET_DPI,
) -> Image.Image:
    """
    Open an image and resize it to exact centimeters
    Mantains aspect relation when only a dimension is given

    Args:
        input_path (str): The path to the image to resize.
        width_cm (float, optional): Image target width.
        height_cm (float, optional): Image target height.
        dpi (int, optional): Dots Per Inch. Defaults to 300.

    Returns:
        Image.Image: Pillow Image object, lives in-memory.
    """

    # Create the canvas to paste the resized image

    page_key = page_type.lower()

    if page_key not in PAGE_SIZES:
        raise ValueError(f"Unsupported page type: {page_type}")

    page_dims_cm = PAGE_SIZES[page_key]
    page_w = cm_to_pixels(page_dims_cm[0], dpi)
    page_h = cm_to_pixels(page_dims_cm[1], dpi)

    canvas = Image.new("RGB", (page_w, page_h), "white")

    if width_cm is None and height_cm is None:
        raise ImageProcessingError("Image dimensions were not validated before processing.")

    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        aspect_ratio = orig_w / orig_h

        target_w = cm_to_pixels(width_cm, dpi) if width_cm else None
        target_h = cm_to_pixels(height_cm, dpi) if height_cm else None

        if target_w and not target_h:
            target_h = int(target_w / aspect_ratio)

        elif target_h and not target_w:
            target_w = int(target_h * aspect_ratio)

        resized_img = img.resize((target_w, target_h), Image.Resampling.BILINEAR)
        resized_img.load()

        # Paste the resized image into the canvas
        margin = cm_to_pixels(2.0, dpi=dpi)
        canvas.paste(resized_img, (margin, margin))

        return canvas


def save_image_for_printing(img: Image.Image, output_path: str, dpi: int = TARGET_DPI) -> None:
    """
    Save the Image object inserting the DPI metadata correctly

    Args:
        img (Image.Image): Resized image.
        output_path (str): Path to save the image.
        dpi (int, optional): Dots per Inch. Defaults to 300.
    """

    img.save(output_path, dpi=(dpi, dpi))
