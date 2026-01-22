from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin, SortableAdminBase 
from .models import Questionario, Secao, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta, RegraEquacao

# 1. Inline para Alternativas (dentro da Pergunta)
class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 1
    verbose_name_plural = "Alternativas"
    classes = ['alternativas-group']

# 2. Inline para Perguntas (dentro da Seção) - Ordenável
class PerguntaInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Pergunta
    extra = 1
    exclude = ('ordem',)

# 3. Admin de Pergunta: Para edição individual e listagem
@admin.register(Pergunta)
class PerguntaAdmin(SortableAdminMixin, admin.ModelAdmin):
    # Alterado: agora referenciamos 'secao' em vez de 'questionario'
    list_display = ('conteudo', 'secao', 'ordem', 'tipo')
    # Para filtrar pelo questionário, usamos a relação secao__questionario
    list_filter = ('secao__questionario', 'tipo')
    inlines = [AlternativaInline]
    exclude = ('ordem',)

    class Media:
        js = ('core/js/hide_alternativas.js',)

# 4. Inline para Seções (dentro do Questionário) - Ordenável
class SecaoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Secao
    extra = 1
    exclude = ('ordem',)

# 5. Admin de Seção: Para gerenciar as Perguntas de uma escala específica
@admin.register(Secao)
class SecaoAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ('titulo', 'questionario', 'ordem', 'layout')
    list_filter = ('questionario',)
    inlines = [PerguntaInline]

# 6. Admin de Questionário: Agora gerencia as Seções (escalas)
@admin.register(Questionario)
class QuestionarioAdmin(SortableAdminBase, admin.ModelAdmin): 
    list_display = ('titulo', 'data_criacao')
    search_fields = ('titulo',)
    inlines = [SecaoInline]

# 7. Registros de Respostas e Regras
@admin.register(RespostaQuestionario)
class RespostaQuestionarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'questionario', 'data_submissao')
    readonly_fields = ('data_submissao',)

admin.site.register(RegraEquacao)
# admin.site.register(RespostaPergunta)

@admin.register(RespostaPergunta)
class RespostaPerguntaAdmin(admin.ModelAdmin):
    # Exibe colunas úteis na listagem principal
    list_display = ('get_usuario', 'pergunta', 'get_resposta', 'get_questionario')
    list_filter = ('pergunta__secao__questionario', 'pergunta__secao')

    # Métodos para buscar dados de chaves estrangeiras distantes
    def get_usuario(self, obj):
        return obj.resposta_questionario.usuario.email
    get_usuario.short_description = 'Usuário'

    def get_questionario(self, obj):
        return obj.resposta_questionario.questionario.titulo
    get_questionario.short_description = 'Questionário'

    def get_resposta(self, obj):
        # Mostra a alternativa escolhida ou o texto digitado
        return obj.alternativa.conteudo if obj.alternativa else obj.resposta_texto
    get_resposta.short_description = 'Resposta'