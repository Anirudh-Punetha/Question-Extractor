from pypdf import PdfReader
from PIL import Image
import tempfile
from pathlib import Path

def pdf_to_images(pdf_path: str):
    reader = PdfReader(pdf_path)
    images = []

    for page in reader.pages:
        img = page.to_image(resolution=200).original
        images.append(img)

    return images