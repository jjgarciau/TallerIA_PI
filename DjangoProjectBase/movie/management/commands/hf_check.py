"""
Comando de diagnostico: revisa que modelos de HuggingFace funcionan con tu
cuenta y tu token. Correr esto primero evita perder tiempo con errores de
'model_not_supported'.

    python manage.py hf_check
"""
from django.core.management.base import BaseCommand

from movie import hf_client


class Command(BaseCommand):
    help = "Verifica que modelos de HuggingFace estan disponibles para tu cuenta"

    def handle(self, *args, **kwargs):
        self.stdout.write(f"Leyendo token desde: {hf_client.ENV_PATH}")

        try:
            client = hf_client.get_client()
        except Exception as e:
            self.stderr.write(str(e))
            return

        self.stdout.write(self.style.SUCCESS("Token cargado correctamente.\n"))

        # ---- 1. Texto -------------------------------------------------
        self.stdout.write("1) Probando modelos de TEXTO (descripciones)...")
        try:
            model, text = hf_client.chat(
                client,
                "Responde solamente con la palabra: listo",
                max_tokens=10,
                on_try=lambda m: self.stdout.write(f"   probando {m} ..."),
            )
            self.stdout.write(self.style.SUCCESS(f"   OK -> {model}"))
            self.stdout.write(f"   respuesta: {text!r}\n")
        except Exception as e:
            self.stderr.write(f"   FALLO: {e}\n")

        # ---- 2. Embeddings --------------------------------------------
        self.stdout.write("2) Probando modelos de EMBEDDINGS (recomendador)...")
        try:
            model, vec = hf_client.embed(
                client,
                "una pelicula de aventuras",
                on_try=lambda m: self.stdout.write(f"   probando {m} ..."),
            )
            self.stdout.write(self.style.SUCCESS(f"   OK -> {model}"))
            self.stdout.write(f"   dimensiones: {vec.shape[0]}\n")
            if vec.shape[0] != hf_client.EMBEDDING_DIM:
                self.stderr.write(
                    f"   OJO: el modelo devuelve {vec.shape[0]} dimensiones y el "
                    f"proyecto espera {hf_client.EMBEDDING_DIM}. "
                    f"Avisa para ajustar el modelo de la base de datos.\n"
                )
        except Exception as e:
            self.stderr.write(f"   FALLO: {e}\n")

        # ---- 3. Imagenes ----------------------------------------------
        self.stdout.write("3) Probando modelos de IMAGEN (posters)...")
        try:
            model, image = hf_client.text_to_image(
                client,
                "Movie poster of a test movie",
                on_try=lambda m: self.stdout.write(f"   probando {m} ..."),
            )
            self.stdout.write(self.style.SUCCESS(f"   OK -> {model}"))
            self.stdout.write(f"   tamano de la imagen: {image.size}\n")
        except Exception as e:
            self.stderr.write(f"   FALLO: {e}\n")

        self.stdout.write(self.style.SUCCESS("Diagnostico terminado."))
