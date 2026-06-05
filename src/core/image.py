import os
from PIL import Image


def cm_to_pixels(cm: float, dpi: int = 300) -> int:
    """
    Converts a size in centimeters to pixels based on the DPI

    Args:
        cm (float): User input size in cm
        dpi (int, optional): Dots Per Inch, pixels fit in one inch. Defaults to 300.

    Returns:
        int: Output pixels
    """

    INCH_PER_CM = 2.54

    return int((cm / INCH_PER_CM) * dpi)


def resize_image_to_cm(input_path: str, width_cm: float = None, height_cm: float = None, dpi: int = 300) -> Image.Image:
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

    if not width_cm and not height_cm:
        raise ValueError("You must specify width or height in centimeters")

    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        aspect_ratio = orig_w / orig_h

        target_w = cm_to_pixels(width_cm, dpi) if width_cm else None
        target_h = cm_to_pixels(height_cm, dpi) if height_cm else None

        if target_w and not target_h:
            target_h = int(target_w / aspect_ratio)

        elif target_h and not target_w:
            target_w = int(target_h * aspect_ratio)

        resized_img = img.resize((target_w, target_h),
                                 Image.Resampling.BILINEAR)

        resized_img.load()

        return resized_img


def save_image_for_printing(img: Image.Image, output_path: str, dpi: int = 300) -> None:
    """
    Save the Image object inserting the DPI metadata correctly

    Args:
        img (Image.Image): Resized image.
        output_path (str): Path to save the image.
        dpi (int, optional): Dots per Inch. Defaults to 300.
    """
    
    img.save(output_path, dpi=(dpi, dpi))