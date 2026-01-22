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
    print('id: ', pk)
    questionario = get_object_or_404(Questionario, pk=pk)
    perguntas_list = questionario.perguntas.all().order_by('ordem')
    
    # Configuramos a paginação (10 por página)
    paginator = Paginator(perguntas_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Inicializa o dicionário de respostas na sessão se não existir
    if 'respostas_temp' not in request.session:
        request.session['respostas_temp'] = {}

    if request.method == 'POST':
        # 1. Coletar respostas da página atual
        # O prefixo 'pergunta_' ajuda a identificar os campos no POST
        for pergunta in page_obj:
            campo_name = f'pergunta_{pergunta.id}'
            valor = request.POST.get(campo_name)
            if valor:
                request.session['respostas_temp'][str(pergunta.id)] = valor
        
        # Marcar a sessão como modificada para garantir o salvamento
        request.session.modified = True

        # 2. Verificar qual botão foi clicado
        acao = request.POST.get('acao')

        if acao == 'proximo' and page_obj.has_next():
            return redirect(f"{request.path}?page={page_obj.next_page_number()}")
        
        elif acao == 'anterior' and page_obj.has_previous():
            return redirect(f"{request.path}?page={page_obj.previous_page_number()}")
        
        elif acao == 'finalizar':
            # Salvar no Banco de Dados
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
            
            # Limpar sessão e redirecionar
            del request.session['respostas_temp']
            messages.success(request, "Questionário enviado com sucesso!")
            return redirect('home')

    # Passamos as respostas já salvas para o template marcar os campos
    respostas_preenchidas = request.session.get('respostas_temp', {})

    context = {
        'questionario': questionario,
        'page_obj': page_obj,
        'respostas_preenchidas': respostas_preenchidas,
        'progresso': int((page_obj.number / paginator.num_pages) * 100)
    }
    return render(request, 'responder_questionario.html', context)

def lista_questionarios(request):
    # Busca todos os questionários cadastrados
    questionarios = Questionario.objects.all().order_by('-data_criacao')
    return render(request, 'lista_questionarios.html', {'questionarios': questionarios})