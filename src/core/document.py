import os
import sys
from typing import List

from docx import Document
from pypdf import PdfReader
from PIL import Image, ImageDraw, ImageFont

from src.core.image import cm_to_pixels
from src.config import TARGET_DPI, PAGE_SIZES


def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts raw text from a Word (.docx) file instantly without launching MS Word

    Args:
        file_path (str): Path to the docx. file

    Returns:
        str: A single string containing all the text extracted from the document paragraphs
    """

    doc = Document(file_path)
    full_text = []

    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)

    return "\n".join(full_text)


def convert_text_to_printable_images(text: str, dpi: int = TARGET_DPI) -> List[Image.Image]:
    """
    Converts a raw text info into a list of lightweight PIL images formatted for printing

    Args:
        text (str): The string content to render
        dpi (int, optional): Target resolution. Defaults to 300.

    Returns:
        List[Image.Image]: A list of PIL Images representing pages
    """

    width_cm, height_cm = PAGE_SIZES["letter"]
    page_w = cm_to_pixels(width_cm, dpi)
    page_h = cm_to_pixels(height_cm, dpi)

    pages = []
    lines = text.split("\n")

    try:
        font = ImageFont.truetype("Arial.ttf", int(12 * (dpi / 72)))

    except IOError:
        font = ImageFont.load_default()

    current_page = Image.new("RGB", (page_w, page_h), "white")
    draw = ImageDraw(current_page)

    margin = int(2 * (dpi / 2.54))  # 2 cm margins
    y_cursor = margin
    line_height = int(16 * (dpi / 72))

    for line in lines:
        if y_cursor + line_height > page_h - margin:
            pages.append(current_page)
            current_page = Image.new("RGB", (page_w, page_h), "white")
            draw = ImageDraw.Draw(current_page)
            y_cursor = margin

        draw.text((margin, y_cursor), line, fill="black", font=font)
        y_cursor += line_height

    pages.append(current_page)

    return pages
