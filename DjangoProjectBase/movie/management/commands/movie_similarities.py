from django.core.management.base import BaseCommand

from movie.models import Movie
from movie import hf_client

# Version adaptada para usar HuggingFace (gratis) en vez de OpenAI.


class Command(BaseCommand):
    help = "Compare two movies and a prompt using free HuggingFace embeddings"

    def handle(self, *args, **kwargs):
        client = hf_client.get_client()

        # Cambia estos titulos por las peliculas que quieras comparar.
        # Nota: la base de datos local solo tiene las 100 primeras peliculas de
        # movies.json, por eso no se usan "La lista de Schindler" ni
        # "El club de la pelea": esas no existen aqui.
        movie1 = Movie.objects.get(title="La captura")
        movie2 = Movie.objects.get(title="Castillo medieval")

        model, emb1 = hf_client.embed(client, movie1.description)
        _, emb2 = hf_client.embed(client, movie2.description)
        self.stdout.write(f"Modelo de embeddings usado: {model}\n")

        self.stdout.write(f"Pelicula 1: {movie1.title}")
        self.stdout.write(f"Pelicula 2: {movie2.title}")

        similarity = hf_client.cosine_similarity(emb1, emb2)
        self.stdout.write(
            f"Similaridad entre '{movie1.title}' y '{movie2.title}': {similarity:.4f}"
        )

        # Comparacion contra un prompt libre
        prompt = "pelicula sobre la Segunda Guerra Mundial"
        self.stdout.write(f"\nPrompt de busqueda: {prompt}")
        _, prompt_emb = hf_client.embed(client, prompt)

        sim1 = hf_client.cosine_similarity(prompt_emb, emb1)
        sim2 = hf_client.cosine_similarity(prompt_emb, emb2)

        self.stdout.write(f"Similitud prompt vs '{movie1.title}': {sim1:.4f}")
        self.stdout.write(f"Similitud prompt vs '{movie2.title}': {sim2:.4f}")
