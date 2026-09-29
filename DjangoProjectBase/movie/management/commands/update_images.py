"""
Genera las imagenes (posters) de las peliculas con la API de HuggingFace
y actualiza el campo image de la base de datos.

Se usa HuggingFace en vez de OpenAI/DALL-E porque la cuenta de OpenAI del
proyecto se quedo sin creditos.

Uso:
    python manage.py update_images                # solo la primera pelicula
    python manage.py update_images --limit 20     # las primeras 20 que falten
    python manage.py update_images --all          # todas las que falten
    python manage.py update_images --all --force  # regenera incluso las que ya existen

Por defecto salta las peliculas que ya tienen su imagen generada, asi que si
se acaba el credito a mitad de camino basta con volver a correr el comando
mas tarde y continua donde iba.
"""
import os

from django.core.management.base import BaseCommand

from movie.models import Movie
from movie.image_utils import safe_image_filename
from movie import hf_client

# Si el error contiene alguna de estas palabras, no tiene sentido seguir
# intentando con las demas peliculas: se acabo el credito o la cuota.
QUOTA_HINTS = ('quota', 'credit', 'payment', 'exceeded', '402', 'insufficient')


class Command(BaseCommand):
    help = "Generate movie posters with the HuggingFace API and update the database"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1,
                            help="Cuantas peliculas procesar (por defecto 1)")
        parser.add_argument('--all', action='store_true',
                            help="Procesar todas las peliculas")
        parser.add_argument('--force', action='store_true',
                            help="Regenerar aunque la imagen ya exista")

    def handle(self, *args, **options):
        client = hf_client.get_client()

        images_folder = 'media/movie/images/'
        os.makedirs(images_folder, exist_ok=True)

        movies = list(Movie.objects.all())
        self.stdout.write(f"Found {len(movies)} movies")

        limit = len(movies) if options['all'] else options['limit']
        force = options['force']

        generated = 0
        skipped = 0

        for movie in movies:
            if generated >= limit:
                break

            filename = safe_image_filename(movie.title)
            full_path = os.path.join(images_folder, filename)

            # Si ya existe la imagen, solo nos aseguramos de que la BD apunte a ella
            if os.path.exists(full_path) and not force:
                relative = os.path.join('movie/images', filename).replace('\\', '/')
                if movie.image != relative:
                    movie.image = relative
                    movie.save()
                skipped += 1
                continue

            try:
                model, image = hf_client.text_to_image(
                    client, f"Movie poster of {movie.title}"
                )
                image.save(full_path)

                movie.image = os.path.join('movie/images', filename).replace('\\', '/')
                movie.save()

                generated += 1
                self.stdout.write(self.style.SUCCESS(
                    f"[{generated}/{limit}] Imagen generada con {model}: {movie.title}"
                ))

            except Exception as e:
                mensaje = str(e).lower()
                self.stderr.write(f"Fallo con '{movie.title}': {e}")
                if any(h in mensaje for h in QUOTA_HINTS):
                    self.stderr.write(
                        "\nParece que se agoto el credito gratuito de HuggingFace. "
                        "Se conserva todo lo generado hasta ahora; puedes volver a "
                        "correr el comando mas adelante y continuara donde iba."
                    )
                    break

        self.stdout.write(self.style.SUCCESS(
            f"\nTerminado. Imagenes generadas: {generated}. "
            f"Peliculas que ya tenian imagen: {skipped}."
        ))
