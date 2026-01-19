from PIL import Image
import io
from django.core.files.base import ContentFile
import os

def clean_image_metadata(uploaded_file):
    """
    Rimuove i metadati EXIF (GPS, data, dispositivo) dalle immagini.
    Supporta JPEG e PNG.
    """
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        return uploaded_file

    img = Image.open(uploaded_file)
    output = io.BytesIO()
    img.save(output, format=img.format)
    output.seek(0)
    return ContentFile(output.read(), name=uploaded_file.name)
