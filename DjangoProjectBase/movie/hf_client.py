"""
Cliente de HuggingFace para el taller.

Se usa HuggingFace (gratis) en lugar de OpenAI porque la cuenta de OpenAI del
proyecto se quedo sin creditos.

HuggingFace ya no sirve todos los modelos desde un unico endpoint: ahora usa
"inference providers", y cada cuenta tiene habilitados unos u otros. Por eso
aqui no se fija un solo modelo: se prueba una lista de candidatos y se usa el
primero que responda. El modelo elegido se recuerda durante la ejecucion para
no repetir la busqueda en cada llamada.
"""
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# huggingface.env vive en la raiz del repositorio, al lado de openAI.env
ENV_PATH = Path(__file__).resolve().parent.parent.parent / 'huggingface.env'

# Modelos de texto (para generar descripciones de peliculas)
CHAT_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3.5-mini-instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "google/gemma-2-9b-it",
    "HuggingFaceH4/zephyr-7b-beta",
]

# Modelos de embeddings. IMPORTANTE: todos son de 384 dimensiones, para que
# los vectores guardados en la base de datos sean comparables entre si.
EMBEDDING_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "BAAI/bge-small-en-v1.5",
    "intfloat/multilingual-e5-small",
    "sentence-transformers/all-MiniLM-L12-v2",
]

# Modelos de generacion de imagenes (posters de peliculas)
IMAGE_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-3.5-large-turbo",
    "black-forest-labs/FLUX.1-dev",
]

EMBEDDING_DIM = 384

# Modelo que ya se comprobo que funciona, por tarea
_CHOSEN = {}


def get_client():
    """Crea el cliente de HuggingFace leyendo el token de huggingface.env."""
    load_dotenv(ENV_PATH)
    token = os.environ.get('hf_token')
    if not token or token.startswith('PEGA_AQUI'):
        raise RuntimeError(
            f"No encontre tu token de HuggingFace. Editalo en: {ENV_PATH}"
        )
    return InferenceClient(token=token)


def _discover(pipeline_tag, limit=8):
    """Ultimo recurso: preguntarle al Hub que modelos hay servidos ahora."""
    try:
        from huggingface_hub import HfApi
        models = HfApi().list_models(
            inference_provider="all",
            pipeline_tag=pipeline_tag,
            sort="trending",
            limit=limit,
        )
        return [m.id for m in models]
    except Exception:
        return []


def _run(task, client, candidates, call, pipeline_tag, on_try=None):
    # Si ya sabemos cual funciona, lo usamos directo
    if task in _CHOSEN:
        return _CHOSEN[task], call(client, _CHOSEN[task])

    errors = []
    for model in list(candidates) + _discover(pipeline_tag):
        try:
            if on_try:
                on_try(model)
            result = call(client, model)
            _CHOSEN[task] = model
            return model, result
        except Exception as e:
            errors.append(f"  - {model}: {str(e)[:160]}")

    raise RuntimeError(
        "Ningun modelo de HuggingFace respondio para la tarea '" + task + "'.\n"
        "Revisa que tengas proveedores habilitados en\n"
        "https://huggingface.co/settings/inference-providers\n"
        "Modelos intentados:\n" + "\n".join(errors)
    )


def chat(client, prompt, max_tokens=300, on_try=None):
    """Devuelve (modelo_usado, texto_generado)."""
    def call(c, model):
        response = c.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=0,
        )
        return response.choices[0].message.content.strip()

    return _run('chat', client, CHAT_MODELS, call, 'text-generation', on_try)


def embed(client, text, on_try=None):
    """Devuelve (modelo_usado, vector_numpy_float32)."""
    def call(c, model):
        arr = np.array(c.feature_extraction(text, model=model), dtype=np.float32)
        # Algunos modelos devuelven un vector por token: promediamos si es 2D
        if arr.ndim > 1:
            arr = arr.mean(axis=0)
        return arr

    return _run('embed', client, EMBEDDING_MODELS, call, 'feature-extraction', on_try)


def text_to_image(client, prompt, on_try=None):
    """Devuelve (modelo_usado, imagen_PIL)."""
    def call(c, model):
        return c.text_to_image(prompt, model=model)

    return _run('image', client, IMAGE_MODELS, call, 'text-to-image', on_try)


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
