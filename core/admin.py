# surveys/admin.py
from django.contrib import admin
# 1. Adicione o SortableAdminBase na importação
from adminsortable2.admin import SortableAdminMixin
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase 
from .models import Questionario, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta, RegraEquacao

class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 1
    verbose_name_plural = "Alternativas"
    classes = ['alternativas-group']

@admin.register(Pergunta)
class PerguntaAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('conteudo', 'questionario', 'ordem', 'tipo')
    list_filter = ('questionario', 'tipo')
    inlines = [AlternativaInline]

    exclude = ('ordem',)

    class Media:
        js = ('core/js/hide_alternativas.js',)

class PerguntaInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Pergunta
    extra = 1

    exclude = ('ordem',)

@admin.register(Questionario)
# 2. Altere a herança para incluir SortableAdminBase
class QuestionarioAdmin(SortableAdminBase, admin.ModelAdmin): 
    list_display = ('titulo', 'data_criacao')
    search_fields = ('titulo',)
    inlines = [PerguntaInline]

@admin.register(RespostaQuestionario)
class RespostaQuestionarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'questionario', 'data_submissao')
    readonly_fields = ('data_submissao',)

admin.site.register(RegraEquacao)