
from django.db import models
from django.conf import settings

class TCLE(models.Model):
    conteudo = models.TextField()
    versao = models.FloatField(default=1.0)
    data_criacao = models.DateTimeField(auto_now_add=True)

class AceiteTCLE(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tcle = models.ForeignKey(TCLE, on_delete=models.CASCADE)
    data_aceite = models.DateTimeField(auto_now_add=True) 
