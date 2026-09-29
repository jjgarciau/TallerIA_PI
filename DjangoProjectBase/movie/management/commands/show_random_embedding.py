import random
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie


class Command(BaseCommand):
    help = "Muestra el embedding almacenado de una pelicula escogida al azar"

    def handle(self, *args, **kwargs):
        movies = list(Movie.objects.all())
        if not movies:
            self.stderr.write("No hay peliculas en la base de datos.")
            return

        movie = random.choice(movies)
        embedding_vector = np.frombuffer(movie.emb, dtype=np.float32)

        self.stdout.write(f"Pelicula seleccionada al azar: {movie.title}")
        self.stdout.write(f"Dimensiones del embedding: {embedding_vector.shape[0]}")
        self.stdout.write(f"Primeros 10 valores: {embedding_vector[:10]}")
        self.stdout.write(f"Embedding completo:\n{embedding_vector}")
