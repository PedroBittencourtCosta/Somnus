
from django.db import models
from django.conf import settings

class Questionario(models.Model):
    titulo = models.CharField(max_length=200) 
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo
    
class Secao(models.Model):
    # Tipos de layout para a seção
    LAYOUT_CHOICES = [('LISTA', 'Lista Vertical'), ('TABELA', 'Tabela (Matriz)')]
    
    questionario = models.ForeignKey(Questionario, related_name='secoes', on_delete=models.CASCADE)
    titulo = models.CharField(blank=True, max_length=200, help_text="Ex: Escala DASS-21 ou Dados Demográficos")
    instrucao = models.TextField(blank=True, help_text="Instruções específicas para esta parte do questionário")
    ordem = models.PositiveIntegerField(default=1)
    layout = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='LISTA')

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Seção'
        verbose_name_plural = 'Seções'

    def __str__(self):
        return f"{self.titulo} - {self.questionario.titulo}"

class Pergunta(models.Model):
    TIPO_CHOICES = [('MC', 'Múltipla Escolha'), ('TX', 'Texto Livre'), ('MX', 'Mista (Opções + Texto)')]

    # Novas opções de validação para tipo MX
    VALIDACAO_MX_CHOICES = [
        ('QUALQUER', 'Pelo menos um (Opção OU Texto)'),
        ('AMBOS', 'Ambos obrigatórios (Opção E Texto)'),
        ('APENAS_OPCAO', 'Obrigatório selecionar opção'),
        ('APENAS_TEXTO', 'Obrigatório preencher texto'),
    ]

    # Campo para configurar a lógica da pergunta mista
    config_mista = models.CharField(
        max_length=15, 
        choices=VALIDACAO_MX_CHOICES, 
        default='QUALQUER',
        help_text="Define a regra de obrigatoriedade para perguntas mistas."
    )

    # ... campos existentes ...
    obrigatoria = models.BooleanField(default=True)
    # Define qual escolha anterior faz esta pergunta aparecer
    depende_de_alternativa = models.ManyToManyField(
        'Alternativa',  
        blank=True,
        related_name='perguntas_dependentes',
        help_text="A pergunta aparecerá se QUALQUER uma destas alternativas for marcada."
    )

    depende_de_texto_de = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='dependentes_por_texto',
        help_text="A pergunta aparecerá se a pergunta selecionada tiver qualquer texto preenchido."
    )
    
    # Agora a pergunta pertence a uma Seção, não mais direto ao Questionário
    secao = models.ForeignKey(Secao, related_name='perguntas', on_delete=models.CASCADE)
    conteudo = models.TextField()
    ordem = models.PositiveIntegerField(default=1)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='MC')

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'

    def __str__(self):
        return self.conteudo


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
        unique_together = ('usuario', 'questionario')

    def __str__(self):
        return f"{self.usuario.username} - {self.questionario.titulo}"

class RespostaPergunta(models.Model):
    resposta_questionario = models.ForeignKey(RespostaQuestionario, related_name='respostas', on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.SET_NULL, null=True, blank=True)
    resposta_texto = models.TextField(null=True, blank=True)

    def __str__(self):
        # Retorna o e-mail do usuário e o início da pergunta para fácil identificação
        return f"Resp: {self.resposta_questionario.usuario.email} - Pergunta: {self.pergunta.conteudo[:30]}..."

class RegraEquacao(models.Model):
    questionario = models.OneToOneField(Questionario, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100) 
    logica = models.TextField(help_text="Explicação ou fórmula para o cálculo")

    class Meta:
        verbose_name = 'Regra de Cálculo'
        verbose_name_plural = 'Regras de Cálculos'

    def __str__(self):
        return self.nome
