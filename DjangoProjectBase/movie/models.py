from django.db import models
import numpy as np

# create your models here

# Vector por defecto para las películas que aún no tienen embedding calculado.
# Son 384 posiciones porque ese es el tamaño del embedding que entrega el modelo
# gratuito de HuggingFace "sentence-transformers/all-MiniLM-L6-v2".
def get_default_array():
    default_arr = np.random.rand(384).astype(np.float32)
    return default_arr.tobytes()


class Movie(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=2000)
    image = models.ImageField(upload_to='movie/images/', default='movie/images/default.JPG')
    url = models.URLField(blank=True)
    genre = models.CharField(blank=True, max_length=250)
    year = models.IntegerField(blank=True, null=True)
    emb = models.BinaryField(default=get_default_array())

    def __str__(self):
        return self.title
