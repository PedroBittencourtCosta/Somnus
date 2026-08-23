
from django.db import models
from django.conf import settings
import uuid
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

class Questionario(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(
        default=True,
        help_text="Controla se o questionário está visível para coleta. "
                  "Desativar é um soft-delete: o registro é preservado no banco."
    )

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

    # Opções de máscaras disponíveis
    MASCARA_CHOICES = [
        ('NENHUMA', 'Nenhuma'),
        ('HORA', 'Hora (00:00)'),
        ('ALTURA', 'Altura (0,00 m)'),
        ('PESO', 'Peso (000,0 kg)'),
        ('DATA', 'Data (00/00/0000)'),
        ('OUTRO', 'Outro'),
    ]

    mascara = models.CharField(max_length=10, choices=MASCARA_CHOICES, default='NENHUMA') # Novo campo
    
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

    identificador = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Nome da variável para o Excel (ex: sexo__, idade__). Se vazio, usará o ID da pergunta."
    )

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'

    def __str__(self):
        if self.identificador:
            return f"[{self.identificador}] {self.conteudo[:50]}..."
        return self.conteudo


class Alternativa(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name='alternativas', on_delete=models.CASCADE)
    conteudo = models.CharField(max_length=255) 
    valor = models.IntegerField() 

    def __str__(self):
        return self.conteudo

class RespostaQuestionario(models.Model):
    pesquisadora = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    data_submissao = models.DateTimeField(auto_now_add=True) 

    # Pseudônimo público — pesquisável, ordenável, indexável (LGPD art. 13 §4º)
    codigo_paciente = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        default=None,  # Será preenchido automaticamente no save()
        verbose_name="Código do Paciente"
    )

    # Nome real criptografado com AES-256 (LGPD art. 46)
    paciente_nome = EncryptedCharField(max_length=255, null=True, verbose_name="Nome do Paciente (protegido)")  # type: ignore

    class Meta:
        verbose_name = 'Resposta de Questionário'
        verbose_name_plural = 'Respostas dos Questionários'
        # unique_together = ('usuario', 'questionario')

    def save(self, *args, **kwargs):
        if not self.codigo_paciente:
            self.codigo_paciente = str(uuid.uuid4()).replace('-', '')[:10].upper()
            while RespostaQuestionario.objects.filter(codigo_paciente=self.codigo_paciente).exists():
                self.codigo_paciente = str(uuid.uuid4()).replace('-', '')[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.codigo_paciente}] {self.paciente_nome} - Pesq: {self.pesquisadora.username}"

class RespostaPergunta(models.Model):
    resposta_questionario = models.ForeignKey(RespostaQuestionario, related_name='respostas', on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Texto livre criptografado com AES-256 (LGPD art. 46)
    resposta_texto = EncryptedTextField(null=True, blank=True)  # type: ignore

    def __str__(self):
        return f"Resp: {self.resposta_questionario.codigo_paciente} - Pergunta: {self.pergunta.conteudo[:30]}..."

class EscalaConfig(models.Model):
    questionarios = models.ManyToManyField(Questionario, related_name='escalas_config', blank=True)
    nome = models.CharField(max_length=100, help_text="Ex: Escala de Depressão DASS-21")
    ativo = models.BooleanField(
        default=True,
        help_text="Soft-delete: escalas inativas não aparecem na interface e não são processadas em novas avaliações."
    )
    
    ESTRATEGIA_CHOICES = [
        ('DYNAMIC', 'Construtor Visual (Somas, Médias e Regras Simples)'),
        ('PSQI', 'Índice de Qualidade de Sono de Pittsburgh (PSQI)'),
        ('IMC', 'Índice de Massa Corporal (IMC)'),
        ('DASS21', 'Depression, Anxiety and Stress Scale (DASS-21)'),
        ('K10', 'Escala de Sofrimento Psicológico de Kessler (K10)'),
        ('SRQ20', 'Self-Reporting Questionnaire (SRQ-20)'),
        ('ESE', 'Escala de Sonolência de Epworth (ESE)'),
        ('AUDIT', 'Alcohol Use Disorder Identification Test (AUDIT)'),
        ('EMSSP', 'Escala Multidimensional de Suporte Social Percebido (EMSSP)'),
    ]
    
    strategy_class = models.CharField(
        max_length=50, 
        choices=ESTRATEGIA_CHOICES,
        default='DYNAMIC', 
        help_text="Selecione 'Construtor Visual' para criar regras pelo sistema, ou escolha uma escala clínica complexa já nativa do sistema."
    )
    
    config_dinamica = models.JSONField(
        blank=True, 
        null=True,
        help_text="Armazena a lógica gerada pela interface do Pesquisador (não precisa ser preenchido manualmente)."
    )

    class Meta:
        verbose_name = 'Configuração de Escala'
        verbose_name_plural = 'Configurações de Escalas'

    def __str__(self):
        return f"{self.nome} ({self.get_strategy_class_display()})"


class ResultadoEscala(models.Model):
    """
    Cache materializado dos resultados de escalas clínicas.

    Gerado automaticamente no momento da submissão do questionário via
    `core.services.calcular_e_salvar_resultados()`. Elimina recálculos
    repetidos ao exibir o dashboard analítico.
    """
    resposta_questionario = models.ForeignKey(
        RespostaQuestionario,
        related_name='resultados_escalas',
        on_delete=models.CASCADE,
        verbose_name='Resposta do Questionário'
    )
    escala_config = models.ForeignKey(
        EscalaConfig,
        on_delete=models.CASCADE,
        verbose_name='Escala Configurada'
    )

    # Resultado completo serializado — preserva todos os sub-scores
    resultado_json = models.JSONField(
        help_text="Dict completo retornado pelo EscalaEngine.processar()"
    )

    # Campos desnormalizados para queries rápidas no dashboard (sem deserializar JSON)
    score_principal = models.FloatField(
        null=True, blank=True,
        help_text="Score numérico principal (ex: psqi_global, k10_total, ese_total)"
    )
    classificacao = models.CharField(
        max_length=150, blank=True, default='',
        help_text="Classificação textual principal (ex: 'Qualidade Ruim', 'Baixo Risco')"
    )

    calculado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('resposta_questionario', 'escala_config')
        verbose_name = 'Resultado de Escala (Cache)'
        verbose_name_plural = 'Resultados de Escalas (Cache)'

    def __str__(self):
        return f"[{self.resposta_questionario.codigo_paciente}] {self.escala_config.nome} → {self.score_principal}"
