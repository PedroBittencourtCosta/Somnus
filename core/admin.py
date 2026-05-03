from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin, SortableAdminBase 
from .models import Questionario, Secao, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta, EscalaConfig

# 1. Inline para Alternativas (Mantido para edição individual da pergunta)
class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 1
    verbose_name_plural = "Alternativas"

# 2. Inline para Perguntas (Dentro da Seção) - Ajustado conforme solicitado
class PerguntaInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Pergunta
    extra = 0
    can_delete = False
    
    # INDISPENSÁVEL: O campo de ordenação deve estar nos fields
    # O Mixin cuidará de escondê-lo e mostrar a barra de arraste no lugar.
    fields = ('ordem', 'conteudo', 'identificador', 'tipo', 'obrigatoria')
    
    sortable_field_name = 'ordem'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Reduzi um pouco a largura para garantir que a barra de arraste apareça à esquerda
        formset.form.base_fields['conteudo'].widget.attrs['style'] = 'width: 450px; height: 40px;'
        return formset

# 3. Admin de Pergunta
@admin.register(Pergunta)
class PerguntaAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('conteudo_curto', 'identificador', 'secao', 'ordem', 'tipo')
    list_editable = ('identificador',)
    list_filter = ('secao__questionario', 'tipo', 'secao')
    inlines = [AlternativaInline]
    exclude = ('ordem',)

    def conteudo_curto(self, obj):
        return obj.conteudo[:80] + '...' if len(obj.conteudo) > 80 else obj.conteudo
    conteudo_curto.short_description = 'Conteúdo da Pergunta'

# 4. Admin de Seção (Onde as perguntas são ordenadas)
@admin.register(Secao)
class SecaoAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ('titulo', 'questionario', 'ordem',)
    list_filter = ('questionario',)
    inlines = [PerguntaInline] # Carrega as perguntas com a barra de ordenação e sem o "remover"

    class Media:
        css = {
            'all': ('core/css/custom_admin.css',)
        }

# 5. Admin de Questionário
class SecaoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Secao
    extra = 1
    sortable_field_name = 'ordem'
    exclude = ('ordem',)

@admin.register(Questionario)
class QuestionarioAdmin(SortableAdminBase, admin.ModelAdmin): 
    list_display = ('titulo', 'data_criacao')
    inlines = [SecaoInline]

# 6. Registros de Respostas (Atualizados para o novo fluxo do Somnus)
@admin.register(RespostaQuestionario)
class RespostaQuestionarioAdmin(admin.ModelAdmin):
    list_display = ('paciente_nome', 'pesquisadora', 'questionario', 'data_submissao')
    search_fields = ('paciente_nome', 'pesquisadora__username')
    readonly_fields = ('data_submissao',)

@admin.register(RespostaPergunta)
class RespostaPerguntaAdmin(admin.ModelAdmin):
    list_display = ('get_pesquisadora', 'get_paciente', 'pergunta', 'get_resposta')
    list_filter = ('pergunta__secao__questionario', 'pergunta__secao')

    def get_pesquisadora(self, obj):
        return obj.resposta_questionario.pesquisadora.username
    get_pesquisadora.short_description = 'Pesquisadora'

    def get_paciente(self, obj):
        return obj.resposta_questionario.paciente_nome
    get_paciente.short_description = 'Paciente'

    def get_resposta(self, obj):
        return obj.alternativa.conteudo if obj.alternativa else obj.resposta_texto
    get_resposta.short_description = 'Resposta'

@admin.register(EscalaConfig)
class EscalaConfigAdmin(admin.ModelAdmin):
    list_display = ('nome', 'questionario', 'strategy_class')
    list_filter = ('strategy_class',)