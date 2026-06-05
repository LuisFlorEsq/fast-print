from typing import List
from PIL import Image

from src.core.image import cm_to_pixels
from src.config import PAGE_SIZES, TARGET_DPI


def create_grid_canvas(images: List[Image.Image], grid_size: int = 4, page_type: str = "letter", dpi: int = TARGET_DPI) -> Image.Image:
    """
    Arranges a list of images into an N-up grid layout on a single blank canvas

    Args:
        images (List[Image.Image]): A list of PIL Image objects to place in grid
        grid_size (int, optional): Total slots in the grid (e.g. 2, 4, 6). Defaults to 4.
        page_type (str, optional): Standard page constraint. Defaults to "letter".
        dpi (int, optional): Target resolution for printing. Defaults to TARGET_DPI.

    Returns:
        Image.Image: A single PIL Image representing the fully assembled grid page.
    """

    if page_type not in PAGE_SIZES:
        raise ValueError(
            f"Unsupported page type: {page_type}. Choose 'letter' or 'A4'")

    if grid_size % 2 != 0 or grid_size < 2:
        raise ValueError(
            "Grid Size must be an even number greater than or equal to 2")

    width_cm, height_cm = PAGE_SIZES[page_type]
    canvas_w = cm_to_pixels(width_cm, dpi)
    canvas_h = cm_to_pixels(height_cm, dpi)

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")

    if grid_size == 2:
        cols, rows = 1, 2
    else:
        cols = 2
        rows = grid_size // 2

    margin = 20  # Margin in pixels

    slot_w = (canvas_w - (margin * (cols + 1))) // cols
    slot_h = (canvas_h - (margin * (rows + 1))) // rows

    image_index = 0
    num_images = len(images)

    for r in range(rows):
        for c in range(cols):
            if image_index >= num_images:
                break  # No more images to paste

            img = images[image_index]

            img.thumbnail((slot_w, slot_h), Image.Resampling.BILINEAR)

            x_offset = margin + c * (slot_w + margin) + \
                (slot_w - img.width) // 2
            y_offset = margin + r * (slot_h + margin) + \
                (slot_h - img.height) // 2

            canvas.paste(img, (x_offset, y_offset))
            image_index += 1
            
    return canvas
