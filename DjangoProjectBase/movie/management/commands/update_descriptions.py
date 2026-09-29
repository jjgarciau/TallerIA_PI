from django.core.management.base import BaseCommand

from movie.models import Movie
from movie import hf_client

# Version adaptada para usar HuggingFace (gratis) en vez de OpenAI, porque la
# cuenta de OpenAI del proyecto se quedo sin creditos. El flujo es el mismo del
# taller: se actualiza solo la primera pelicula (el break sigue ahi).


class Command(BaseCommand):
    help = "Update movie descriptions using a free HuggingFace model"

    def handle(self, *args, **kwargs):
        # Cliente de HuggingFace (lee el token de huggingface.env)
        client = hf_client.get_client()

        # Instruccion que guia la respuesta del modelo
        instruction = (
            "Vas a actuar como un aficionado del cine que sabe describir de forma clara, "
            "concisa y precisa cualquier pelicula en menos de 200 palabras. La descripcion "
            "debe incluir el genero de la pelicula y cualquier informacion adicional que sirva "
            "para crear un sistema de recomendacion."
        )

        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies")

        for movie in movies:
            self.stdout.write(f"Processing: {movie.title}")
            try:
                prompt = (
                    f"{instruction} "
                    f"Vas a actualizar la descripcion '{movie.description}' "
                    f"de la pelicula '{movie.title}'."
                )

                print(f"Title: {movie.title}")
                print(f"Original Description: {movie.description}")

                # Devuelve el modelo que respondio y el texto generado
                model, updated_description = hf_client.chat(client, prompt)

                print(f"Model used: {model}")
                print(f"Updated Description: {updated_description}")

                movie.description = updated_description
                movie.save()

                self.stdout.write(self.style.SUCCESS(f"Updated: {movie.title}"))

            except Exception as e:
                self.stderr.write(f"Failed for {movie.title}: {e}")

            # No quitar el break: solo se procesa la primera pelicula
            break
