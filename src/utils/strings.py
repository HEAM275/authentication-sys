# src/utils/strings.py
import re

def sanitize_string(value: str) -> str:
    """Elimina caracteres potencialmente peligrosos."""
    return re.sub(r'[<>"\'&]', '', value)

def slugify(text: str) -> str:
    """Convierte texto a formato URL-friendly."""
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).lower()
    return re.sub(r'[\s-]+', '-', text).strip('-')