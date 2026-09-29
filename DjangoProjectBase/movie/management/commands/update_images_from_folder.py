"""
Asigna a cada pelicula la imagen que ya existe en media/movie/images/,
buscando archivos con el nombre m_<titulo>.png.

Sirve para cuando las imagenes se generaron aparte (con la API, con otra
herramienta, o descargadas) y solo falta enlazarlas en la base de datos.

    python manage.py update_images_from_folder
"""
import os

from django.core.management.base import BaseCommand

from movie.models import Movie
from movie.image_utils import safe_image_filename


class Command(BaseCommand):
    help = "Assign images from media/movie/images/ to the movies in the database"

    def handle(self, *args, **kwargs):
        images_folder = os.path.join('media', 'movie', 'images')

        if not os.path.isdir(images_folder):
            self.stderr.write(f"No existe la carpeta '{images_folder}'.")
            return

        available = set(os.listdir(images_folder))

        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies")
        self.stdout.write(f"Archivos en la carpeta: {len(available)}")

        updated = 0
        sin_imagen = []

        for movie in movies:
            # Nombre limpio (el que usa el comando que genera con la API)
            filename = safe_image_filename(movie.title)

            # Por compatibilidad, tambien aceptamos el nombre sin limpiar
            alternativo = f"m_{movie.title}.png"

            elegido = None
            if filename in available:
                elegido = filename
            elif alternativo in available:
                elegido = alternativo

            if elegido:
                movie.image = os.path.join('movie/images', elegido).replace('\\', '/')
                movie.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated image for: {movie.title}"))
            else:
                sin_imagen.append(movie.title)

        if sin_imagen:
            self.stdout.write(f"\nPeliculas sin imagen en la carpeta: {len(sin_imagen)}")
            for titulo in sin_imagen[:5]:
                self.stdout.write(f"   - {titulo}")
            if len(sin_imagen) > 5:
                self.stdout.write(f"   ... y {len(sin_imagen) - 5} mas")
            self.stdout.write(
                "   (esas conservan la imagen por defecto; puedes generarlas con "
                "'python manage.py update_images --all')"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nTerminado. Imagenes asignadas: {updated}."
        ))
