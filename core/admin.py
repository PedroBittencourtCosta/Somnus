# surveys/admin.py
from django.contrib import admin
from .models import Questionario, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta, RegraEquacao

class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 4  # Quantidade de espaços em branco para novas alternativas

@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ('conteudo', 'questionario', 'ordem', 'tipo')
    list_filter = ('questionario', 'tipo')
    inlines = [AlternativaInline]

@admin.register(Questionario)
class QuestionarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_criacao')

@admin.register(RespostaQuestionario)
class RespostaQuestionarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'questionario', 'data_submissao')
    readonly_fields = ('data_submissao',)

admin.site.register(RegraEquacao)
