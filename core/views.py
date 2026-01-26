from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import csv
from .decorators import medico_ou_admin_required

from ethics.models import TCLE, AceiteTCLE
from .models import Questionario, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta

def index_view(request: HttpRequest):
    return render(request, 'home.html')

@login_required
def responder_questionario(request, pk):
    questionario = get_object_or_404(Questionario, pk=pk)

    # 1. Busca a versão mais recente do TCLE
    ultimo_tcle = TCLE.objects.order_by('-versao').first()
    
    # 2. Verifica se o usuário já aceitou esta versão específica
    # Se NÃO houver TCLE cadastrado no banco, não podemos exibir o modal
    if not ultimo_tcle:
        # Você pode decidir se permite responder sem TCLE ou se mostra um erro
        messages.warning(request, "Atenção: Nenhum Termo de Consentimento (TCLE) foi encontrado no sistema.")
        # Segue a lógica normal se não houver termo
        ja_aceitou = True 
    else:
        ja_aceitou = AceiteTCLE.objects.filter(usuario=request.user, tcle=ultimo_tcle).exists()

    # 3. Se não aceitou, enviamos o conteúdo do TCLE para o modal
    if not ja_aceitou and ultimo_tcle:
        # Reutilizamos a lógica de seções mas enviamos a flag do modal
        context = {
            'questionario': questionario,
            'exibir_tcle': True,
            'tcle': ultimo_tcle,
        }
        # Renderiza a mesma página, mas o JS abrirá o modal
        return render(request, 'responder_questionario.html', context)
    
    # TRAVA DE RESPOSTA ÚNICA
    ja_respondeu = RespostaQuestionario.objects.filter(
        usuario=request.user, 
        questionario=questionario
    ).exists()

    if ja_respondeu:
        messages.info(request, "Você já completou esta avaliação. Obrigado pela participação!")
        return redirect('home')

    secoes_list = questionario.secoes.all().order_by('ordem')
    
    paginator = Paginator(secoes_list, 1)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    secao_atual = page_obj.object_list[0] if page_obj.object_list else None

    if 'respostas_temp' not in request.session:
        request.session['respostas_temp'] = {}

    if request.method == 'POST':
        for pergunta in secao_atual.perguntas.all():
            # Capturamos tanto o valor da múltipla escolha quanto o texto
            valor_id = request.POST.get(f'pergunta_{pergunta.id}')
            valor_texto = request.POST.get(f'pergunta_{pergunta.id}_texto')
            
            # Armazenamos um dicionário para suportar os dois valores na sessão
            request.session['respostas_temp'][str(pergunta.id)] = {
                'alternativa': valor_id,
                'texto': valor_texto
            }
        
        request.session.modified = True
        acao = request.POST.get('acao')

        if acao == 'proximo' and page_obj.has_next():
            return redirect(f"{request.path}?page={page_obj.next_page_number()}")
        elif acao == 'anterior' and page_obj.has_previous():
            return redirect(f"{request.path}?page={page_obj.previous_page_number()}")
        elif acao == 'finalizar':
            res_quest = RespostaQuestionario.objects.create(usuario=request.user, questionario=questionario)
            respostas_cache = request.session.get('respostas_temp', {})
            
            for p_id, valores in respostas_cache.items():
                pergunta = Pergunta.objects.get(id=p_id)
                alt = None
                if valores.get('alternativa'):
                    alt = Alternativa.objects.get(id=valores['alternativa'])
                
                RespostaPergunta.objects.create(
                    resposta_questionario=res_quest,
                    pergunta=pergunta,
                    alternativa=alt,
                    resposta_texto=valores.get('texto')
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
    questionarios = Questionario.objects.all().order_by('-data_criacao')
    
    # Se o usuário estiver logado, buscamos os IDs dos questionários que ele já respondeu
    respondidos = []
    if request.user.is_authenticated:
        respondidos = RespostaQuestionario.objects.filter(
            usuario=request.user
        ).values_list('questionario_id', flat=True)
        
    return render(request, 'lista_questionarios.html', {
        'questionarios': questionarios,
        'respondidos': respondidos
    })



@login_required
@medico_ou_admin_required
def dashboard_respostas(request):
    # Ordenação decrescente por data de submissão
    respostas_list = RespostaQuestionario.objects.select_related('usuario', 'questionario').all().order_by('-data_submissao')
    
    # Paginação: 10 itens por página
    paginator = Paginator(respostas_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard_respostas.html', {'respostas': page_obj})

@login_required
@medico_ou_admin_required
def exportar_respostas_csv(request, pk):
    # Busca a resposta específica do questionário
    res_quest = get_object_or_404(RespostaQuestionario, pk=pk)
    
    response = HttpResponse(content_type='text/csv')
    filename = f"somnus_{res_quest.usuario.username}_{res_quest.id}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf8')) 

    writer = csv.writer(response, delimiter=';')
    
    # Cabeçalho do arquivo
    writer.writerow(['Pergunta', 'Resposta Selecionada', 'Texto Adicional/Livre', 'Valor/Score'])

    # Busca todas as respostas das perguntas deste questionário específico
    respostas_perguntas = RespostaPergunta.objects.filter(resposta_questionario=res_quest).select_related('pergunta', 'alternativa')

    for rp in respostas_perguntas:
        writer.writerow([
            rp.pergunta.conteudo,
            rp.alternativa.conteudo if rp.alternativa else "N/A",
            rp.resposta_texto if rp.resposta_texto else "",
            rp.alternativa.valor if rp.alternativa else ""
        ])

    return response