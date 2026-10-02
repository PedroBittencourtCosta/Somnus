
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

    # Como a via do comprovante chegou ao participante (RN03).
    # O e-mail usado no envio NÃO é armazenado — apenas o meio de entrega.
    ENTREGA_CHOICES = [
        ('IMPRESSO', 'Impresso'),
        ('EMAIL', 'E-mail'),
        ('ANOTADO', 'Código anotado pelo participante'),
    ]
    comprovante_entregue_por = models.CharField(
        max_length=10, choices=ENTREGA_CHOICES, blank=True, default='',
        verbose_name='Entrega do comprovante'
    )

    class Meta:
        verbose_name = 'Aceite de TCLE'
        verbose_name_plural = 'Aceites de TCLE'

    def __str__(self):
        # Agora identificamos pelo nome do paciente gravado na resposta
        return f"Consentimento: {self.resposta_questionario.codigo_paciente} - v{self.tcle.versao}"

class RevogacaoConsentimento(models.Model):
    """
    Registro mínimo de que um consentimento foi retirado (RN05 / RF-014).

    A coleta é excluída de forma definitiva; aqui fica só o necessário para
    auditoria. Nenhum dado do participante (nome, respostas, resultados) é
    guardado — o código isolado não se liga a mais nada após a exclusão.
    """
    codigo_paciente = models.CharField(max_length=12, verbose_name='Código do participante')
    questionario_titulo = models.CharField(max_length=255, verbose_name='Questionário')
    tcle_versao = models.FloatField(null=True, blank=True, verbose_name='Versão do TCLE aceita')
    data_coleta = models.DateTimeField(verbose_name='Data da coleta')
    data_revogacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da revogação')
    revogado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='revogacoes_registradas',
        verbose_name='Registrado por'
    )

    class Meta:
        verbose_name = 'Revogação de consentimento'
        verbose_name_plural = 'Revogações de consentimento'
        ordering = ['-data_revogacao']

    def __str__(self):
        return f"Revogação {self.codigo_paciente} em {self.data_revogacao:%d/%m/%Y}"
