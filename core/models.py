
from django.db import models
from django.conf import settings

class Questionario(models.Model):
    titulo = models.CharField(max_length=200) 
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Pergunta(models.Model):
    TIPO_CHOICES = [('MC', 'Múltipla Escolha'), ('TX', 'Texto Livre')]
    
    questionario = models.ForeignKey(Questionario, related_name='perguntas', on_delete=models.CASCADE)
    conteudo = models.TextField()
    ordem = models.PositiveIntegerField(default=1, help_text="A ordem será sugerida automaticamente.")
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='MC')

    class Meta:
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'
        # ESTA LINHA ABAIXO É O QUE RESOLVE O ERRO:
        ordering = ['ordem']

    def __str__(self):
        return self.conteudo
    
    def save(self, *args, **kwargs):
        # Se for uma nova pergunta (não tem ID ainda) e a ordem for 0
        if not self.pk and self.ordem == 0:
            ultimo = Pergunta.objects.filter(questionario=self.questionario).order_by('-ordem').first()
            if ultimo:
                self.ordem = ultimo.ordem + 1
            else:
                self.ordem = 1
        super().save(*args, **kwargs)


class Alternativa(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name='alternativas', on_delete=models.CASCADE)
    conteudo = models.CharField(max_length=255) 
    valor = models.IntegerField() 

    def __str__(self):
        return self.conteudo

class RespostaQuestionario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    data_submissao = models.DateTimeField(auto_now_add=True) 

    class Meta:
        verbose_name = 'Resposta de Questionário'
        verbose_name_plural = 'Respostas dos Questionários'

class RespostaPergunta(models.Model):
    resposta_questionario = models.ForeignKey(RespostaQuestionario, related_name='respostas', on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.SET_NULL, null=True, blank=True)
    resposta_texto = models.TextField(null=True, blank=True)

class RegraEquacao(models.Model):
    questionario = models.OneToOneField(Questionario, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100) 
    logica = models.TextField(help_text="Explicação ou fórmula para o cálculo")

    class Meta:
        verbose_name = 'Regra de Cálculo'
        verbose_name_plural = 'Regras de Cálculos'

    def __str__(self):
        return self.nome
