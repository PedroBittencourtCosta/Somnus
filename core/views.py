from datetime import date
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import csv

from core.Scaleprocessor import AUDITCalculator, DASS21Calculator, EMSSPCalculator, ESECalculator, K10Calculator, PSQICalculator, SRQ20Calculator, SafeParser
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



def get_answers_by_section(respostas_queryset, section_id):
    """Filtra respostas de uma seção e mapeia pela posição relativa."""
    respostas_secao = respostas_queryset.filter(
        pergunta__secao_id=section_id
    ).order_by('pergunta__ordem')
    
    return {i+1: rp.alternativa.valor for i, rp in enumerate(respostas_secao) if rp.alternativa}


@login_required
@medico_ou_admin_required
def exportar_respostas_csv(request, pk):
    res_quest = get_object_or_404(RespostaQuestionario, pk=pk)
    user = res_quest.usuario
    
    # Carregamento e Mapeamento (Lógica defensiva contra NoneType)
    respostas_qs = RespostaPergunta.objects.filter(
        resposta_questionario=res_quest
    ).select_related('pergunta', 'alternativa')

    # --- NOVO MAPEAMENTO HÍBRIDO ---
    answers_map = {}
    for rp in respostas_qs:
        identificador = rp.pergunta.identificador
        if identificador:
            # Se tiver alternativa (DASS, K10), pega o valor numérico
            if rp.alternativa:
                answers_map[identificador] = rp.alternativa.valor
            # Se for texto (Peso, Altura, Horários), pega o texto bruto
            elif rp.resposta_texto:
                answers_map[identificador] = rp.resposta_texto

    # PROCESSAMENTO MODULAR [cite: 256, 276]
    scores_dass  = DASS21Calculator.calculate(answers_map)
    scores_k10   = K10Calculator.calculate(answers_map)
    scores_srq   = SRQ20Calculator.calculate(answers_map)
    scores_ese   = ESECalculator.calculate(answers_map)   # Novo
    scores_audit = AUDITCalculator.calculate(answers_map) # Novo
    scores_emssp = EMSSPCalculator.calculate(answers_map)
    scores_psqi = PSQICalculator.calculate(answers_map)
    
    # Cálculo Extra: IMC (Seção 7.2) 
    peso = SafeParser.to_float(answers_map.get('peso', 0))
    altura = SafeParser.to_float(answers_map.get('altura', 0))
    
    imc = round(peso / (altura ** 2), 2) if altura > 0 else 0

    # GERAÇÃO DO CSV
    response = HttpResponse(content_type='text/csv')
    filename = f"somnus_completo_{user.username}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf8')) 
    writer = csv.writer(response, delimiter=';')
    
    # BLOCO: SCORES CALCULADOS
    writer.writerow(['RESUMO DOS SCORES'])
    writer.writerow(['Escala', 'Score Total', 'Status/Classificação'])
    
    # Saúde Mental
    writer.writerow(['DASS21_DEPRESSAO', scores_dass['dass_depressao'], "0-21"])
    writer.writerow(['DASS21_ANSIEDADE', scores_dass['dass_ansiedade'], "0-21"])
    writer.writerow(['DASS21_ESTRESSE',  scores_dass['dass_estresse'],  "0-21"])
    writer.writerow(['K10_TOTAL',        scores_k10['k10_total'],       scores_k10['k10_classificacao']])
    writer.writerow(['SRQ20_TOTAL',      scores_srq['srq_total'],       scores_srq['srq_status']])
    
    # Hábitos e Sono (Caminho Rápido)
    writer.writerow(['ESE_EPWORTH',      scores_ese['ese_total'],       scores_ese['ese_status']])
    writer.writerow(['AUDIT_ALCOOL',     scores_audit['audit_total'],   scores_audit['audit_status']])

    # Suporte Social
    writer.writerow(['SUPORTE_FAMILIA', scores_emssp['suporte_familia'], "Máx 28"])
    writer.writerow(['SUPORTE_AMIGOS',  scores_emssp['suporte_amigos'],  "Máx 28"])
    writer.writerow(['SUPORTE_OUTROS',  scores_emssp['suporte_outros'],  "Máx 28"])
    writer.writerow(['SUPORTE_TOTAL',   scores_emssp['suporte_total'],   "Máx 84"])

    writer.writerow(['RESUMO DOS SCORES (PITTSBURGH E SAÚDE)'])
    writer.writerow(['Indicador', 'Score', 'Classificação'])
    writer.writerow(['PSQI_GLOBAL', scores_psqi['psqi_global'], scores_psqi['psqi_status']])
    writer.writerow(['IMC_ATUAL', imc, "kg/m²"])

    # Detalhamento dos componentes do PSQI para o seu artigo
    for i, comp in enumerate(scores_psqi['psqi_componentes'], 1):
        writer.writerow([f'PSQI_COMPONENTE_{i}', comp, "0 a 3"])
    
    writer.writerow([]) # Separador

    # BLOCO: DETALHAMENTO DAS RESPOSTAS (Corrigido para evitar crash)
    writer.writerow(['DETALHAMENTO'])
    writer.writerow(['DETALHAMENTO COMPLETO'])
    for rp in respostas_qs.order_by('pergunta__ordem'):
        # Aqui garantimos que o CSV mostre o texto se não houver alternativa
        valor_exibicao = rp.alternativa.valor if rp.alternativa else rp.resposta_texto
        writer.writerow([
            rp.pergunta.identificador or f"ID_{rp.pergunta.id}",
            rp.pergunta.conteudo[:80],
            valor_exibicao
        ])
    return response