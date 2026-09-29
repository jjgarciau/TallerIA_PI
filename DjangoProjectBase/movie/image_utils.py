"""
Utilidades para los archivos de imagen de las peliculas.

Los titulos de algunas peliculas traen caracteres que Windows no permite en
nombres de archivo (por ejemplo ':' o '?'), asi que hay que limpiarlos antes
de guardar. Esta funcion la usan tanto el comando que genera las imagenes con
la API como el que las carga desde la carpeta, para que los nombres coincidan.
"""
import re

# Caracteres que Windows no acepta en un nombre de archivo
INVALID_CHARS = r'<>:"/\|?*'


def safe_image_filename(title):
    """Convierte 'The '?' Motorist' en 'm_The _ Motorist.png'."""
    clean = title
    for ch in INVALID_CHARS:
        clean = clean.replace(ch, '_')
    # Colapsa espacios raros y recorta, sin dejar puntos al final (Windows)
    clean = re.sub(r'\s+', ' ', clean).strip().rstrip('.')
    # Nombre de archivo maximo razonable
    clean = clean[:120]
    return f"m_{clean}.png"
