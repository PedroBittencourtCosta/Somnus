from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Questionario, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta

def index_view(request: HttpRequest):
    return render(request, 'home.html')

@login_required
def responder_questionario(request, pk):
    questionario = get_object_or_404(Questionario, pk=pk)
    
    # Ordenamos as seções pela ordem definida no Admin
    secoes_list = questionario.secoes.all().order_by('ordem')
    
    # Paginator de 1 item por página (uma seção por vez)
    paginator = Paginator(secoes_list, 1)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # A seção atual que será renderizada
    secao_atual = page_obj.object_list[0] if page_obj.object_list else None

    # Inicializa o cache de respostas na sessão
    if 'respostas_temp' not in request.session:
        request.session['respostas_temp'] = {}

    if request.method == 'POST':
        # 1. Salva as respostas da seção atual no cache da sessão
        for pergunta in secao_atual.perguntas.all():
            campo_name = f'pergunta_{pergunta.id}'
            valor = request.POST.get(campo_name)
            if valor:
                request.session['respostas_temp'][str(pergunta.id)] = valor
        
        request.session.modified = True
        acao = request.POST.get('acao')

        # 2. Lógica de navegação
        if acao == 'proximo' and page_obj.has_next():
            return redirect(f"{request.path}?page={page_obj.next_page_number()}")
        
        elif acao == 'anterior' and page_obj.has_previous():
            return redirect(f"{request.path}?page={page_obj.previous_page_number()}")
        
        elif acao == 'finalizar':
            # Persistência final no Banco de Dados
            res_quest = RespostaQuestionario.objects.create(
                usuario=request.user,
                questionario=questionario
            )
            
            respostas_cache = request.session.get('respostas_temp', {})
            
            for p_id, valor in respostas_cache.items():
                pergunta = Pergunta.objects.get(id=p_id)
                if pergunta.tipo == 'MC':
                    alternativa = Alternativa.objects.get(id=valor)
                    RespostaPergunta.objects.create(
                        resposta_questionario=res_quest,
                        pergunta=pergunta,
                        alternativa=alternativa
                    )
                else:
                    RespostaPergunta.objects.create(
                        resposta_questionario=res_quest,
                        pergunta=pergunta,
                        resposta_texto=valor
                    )
            
            del request.session['respostas_temp']
            messages.success(request, "Avaliação concluída com sucesso!")
            return redirect('home')

    context = {
        'questionario': questionario,
        'secao': secao_atual,
        'page_obj': page_obj,
        'respostas_preenchidas': request.session.get('respostas_temp', {}),
        'progresso': int((page_obj.number / paginator.num_pages) * 100)
    }
    return render(request, 'responder_questionario.html', context)

def lista_questionarios(request):
    # Busca todos os questionários cadastrados
    questionarios = Questionario.objects.all().order_by('-data_criacao')
    return render(request, 'lista_questionarios.html', {'questionarios': questionarios})