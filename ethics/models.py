
from django.db import models
from django.conf import settings

class TCLE(models.Model):
    conteudo = models.TextField()
    versao = models.FloatField(default=1.0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Versão {self.versao}"

class AceiteTCLE(models.Model):
    # AJUSTE: Relacionamos o aceite à RESPOSTA específica do paciente
    resposta_questionario = models.OneToOneField(
        'core.RespostaQuestionario', 
        on_delete=models.CASCADE, 
        related_name='aceite'
    )
    tcle = models.ForeignKey(TCLE, on_delete=models.CASCADE)
    data_aceite = models.DateTimeField(auto_now_add=True) 

    class Meta:
        verbose_name = 'Aceite de TCLE'
        verbose_name_plural = 'Aceites de TCLE'

    def __str__(self):
        # Agora identificamos pelo nome do paciente gravado na resposta
        return f"Consentimento: {self.resposta_questionario.paciente_nome} - v{self.tcle.versao}"