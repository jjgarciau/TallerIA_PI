from django.core.management.base import BaseCommand

from movie.models import Movie
from movie import hf_client

# Version adaptada para usar HuggingFace (gratis) en vez de OpenAI.


class Command(BaseCommand):
    help = "Generate and store embeddings for all movies in the database"

    def handle(self, *args, **kwargs):
        client = hf_client.get_client()

        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies in the database")

        first = True
        for movie in movies:
            try:
                model, emb = hf_client.embed(client, movie.description)
                if first:
                    self.stdout.write(f"Model used: {model} ({emb.shape[0]} dimensiones)")
                    first = False

                # Se almacena el embedding como binario en la base de datos
                movie.emb = emb.tobytes()
                movie.save()
                self.stdout.write(self.style.SUCCESS(f"Embedding stored for: {movie.title}"))
            except Exception as e:
                self.stderr.write(f"Failed to generate embedding for {movie.title}: {e}")

        self.stdout.write(self.style.SUCCESS("Finished generating embeddings for all movies"))
