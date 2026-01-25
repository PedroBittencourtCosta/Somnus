
from django.db import models
from django.conf import settings

class TCLE(models.Model):
    conteudo = models.TextField()
    versao = models.FloatField(default=1.0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Versão {self.versao}"

class AceiteTCLE(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tcle = models.ForeignKey(TCLE, on_delete=models.CASCADE)
    data_aceite = models.DateTimeField(auto_now_add=True) 

    class Meta:
        verbose_name = 'Aceite de TCLE'
        verbose_name_plural = 'Aceites de TCLE'
        # AJUSTE 1: Garante que o usuário aceite cada versão apenas uma vez
        unique_together = ('usuario', 'tcle')

    # AJUSTE 2: Facilita a auditoria no Django Admin
    def __str__(self):
        return f"Aceite: {self.usuario.email} - v{self.tcle.versao}"