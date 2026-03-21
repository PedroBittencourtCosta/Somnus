
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from core.Scaleprocessor import AUDITCalculator, DASS21Calculator, EMSSPCalculator, ESECalculator, K10Calculator, PSQICalculator, SRQ20Calculator, SafeParser

from ethics.models import TCLE, AceiteTCLE
from .models import Questionario, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta

def index_view(request: HttpRequest):
    return render(request, 'home.html')

@login_required
def responder_questionario(request, pk):
    questionario = get_object_or_404(Questionario, pk=pk)
    ultimo_tcle = TCLE.objects.order_by('-versao').first()

    # --- LÓGICA TCLE: POR ATENDIMENTO (SESSÃO) ---
    tcle_aceito_na_sessao = request.session.get('tcle_aceito', False)

    if not tcle_aceito_na_sessao and ultimo_tcle:
        context = {
            'questionario': questionario,
            'exibir_tcle': True,
            'tcle': ultimo_tcle,
        }
        return render(request, 'responder_questionario.html', context)
    
    # Configuração da paginação e sessões
    secoes_list = questionario.secoes.all().order_by('ordem')
    paginator = Paginator(secoes_list, 1)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    secao_atual = page_obj.object_list[0] if page_obj.object_list else None

    if 'respostas_temp' not in request.session:
        request.session['respostas_temp'] = {}

    if request.method == 'POST':
        acao = request.POST.get('acao')

        # Aceite do TCLE
        if acao == 'aceitar_tcle':
            request.session['tcle_aceito'] = True
            request.session.modified = True
            return redirect(request.path)

        # Salva respostas da página atual na sessão
        if secao_atual:
            for pergunta in secao_atual.perguntas.all():
                request.session['respostas_temp'][str(pergunta.id)] = {
                    'alternativa': request.POST.get(f'pergunta_{pergunta.id}'),
                    'texto': request.POST.get(f'pergunta_{pergunta.id}_texto'),
                    'identificador': pergunta.identificador 
                }
        
        request.session.modified = True

        if acao == 'proximo' and page_obj.has_next():
            return redirect(f"{request.path}?page={page_obj.next_page_number()}")
        elif acao == 'anterior' and page_obj.has_previous():
            return redirect(f"{request.path}?page={page_obj.previous_page_number()}")
        
        elif acao == 'finalizar':
            respostas_cache = request.session.get('respostas_temp', {})
            ultimo_tcle = TCLE.objects.order_by('-versao').first()

            # 1. Extraímos o nome do paciente do cache (procurando pelo identificador técnico 'nome')
            nome_extraido = "Não informado"
            for v in respostas_cache.values():
                if v.get('identificador') == 'nome':
                    # Pega o texto preenchido na pergunta de nome
                    nome_extraido = v.get('texto') or "Não informado"
                    break

           # 2. Criamos a RespostaQuestionario (Modelo novo)
            res_quest = RespostaQuestionario.objects.create(
                pesquisadora=request.user, # Aluna logada
                questionario=questionario,
                paciente_nome=nome_extraido
            )

            # 3. NOVO: Relacionamos a resposta ao TCLE aceito nesta sessão
            if ultimo_tcle:
                AceiteTCLE.objects.create(
                    resposta_questionario=res_quest,
                    tcle=ultimo_tcle
                )
            
            # 4. Salva todas as respostas (incluindo idade, sexo, etc., que agora são perguntas)
            for p_id, valores in respostas_cache.items():
                pergunta = Pergunta.objects.get(id=p_id)
                alt = None
                if valores.get('alternativa'):
                    try:
                        alt = Alternativa.objects.get(id=valores['alternativa'])
                    except (Alternativa.DoesNotExist, ValueError):
                        alt = None
                
                RespostaPergunta.objects.create(
                    resposta_questionario=res_quest,
                    pergunta=pergunta,
                    alternativa=alt,
                    resposta_texto=valores.get('texto')
                )
            
            # 5. Limpeza da sessão para o próximo atendimento
            del request.session['respostas_temp']
            request.session['tcle_aceito'] = False
            request.session.modified = True

            messages.success(request, f"Avaliação de {nome_extraido} concluída!")
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
            pesquisadora=request.user
        ).values_list('questionario_id', flat=True)
        
    return render(request, 'lista_questionarios.html', {
        'questionarios': questionarios,
        'respondidos': respondidos
    })



@login_required
def dashboard_respostas(request):
    # Ordenação decrescente por data de submissão
    respostas_list = RespostaQuestionario.objects.select_related('pesquisadora', 'questionario').all().order_by('-data_submissao')
    
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
def exportar_respostas_excel(request, pk):
    # 1. BUSCA DE DADOS
    res_quest = get_object_or_404(RespostaQuestionario, pk=pk)
    pesquisadora = res_quest.pesquisadora 
    
    respostas_qs = RespostaPergunta.objects.filter(
        resposta_questionario=res_quest
    ).select_related('pergunta', 'alternativa')

    # 2. MAPEAMENTO HÍBRIDO
    answers_map = {}
    for rp in respostas_qs:
        identificador = rp.pergunta.identificador
        if identificador:
            if rp.alternativa:
                answers_map[identificador] = rp.alternativa.valor
            elif rp.resposta_texto:
                answers_map[identificador] = rp.resposta_texto

    # 3. PROCESSAMENTO DAS ESCALAS (Certifique-se que estas classes existem no seu utils.py)
    scores_dass  = DASS21Calculator.calculate(answers_map)
    scores_k10   = K10Calculator.calculate(answers_map)
    scores_srq   = SRQ20Calculator.calculate(answers_map)
    scores_ese   = ESECalculator.calculate(answers_map)
    scores_audit = AUDITCalculator.calculate(answers_map)
    scores_emssp = EMSSPCalculator.calculate(answers_map)
    scores_psqi  = PSQICalculator.calculate(answers_map)
    
    peso = SafeParser.to_float(answers_map.get('peso', 0))
    altura = SafeParser.to_float(answers_map.get('altura', 0))
    imc = round(peso / (altura ** 2), 2) if altura > 0 else 0

    # 4. CRIAÇÃO DO EXCEL
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatório de Avaliação"

    # Estilos
    azul_somnus = PatternFill(start_color='1A365D', end_color='1A365D', fill_type='solid')
    cinza_claro = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
    fonte_branca = Font(color='FFFFFF', bold=True)
    center_align = Alignment(horizontal='center', vertical='center')

    # Cabeçalho
    ws.merge_cells('A1:C1')
    ws['A1'] = "SOMNUS - RELATÓRIO TÉCNICO"
    ws['A1'].font = Font(size=14, bold=True, color='1A365D')
    ws['A1'].alignment = center_align

    ws.append(['Paciente:', res_quest.paciente_nome])
    ws.append(['Pesquisadora:', pesquisadora.username])
    ws.append(['Data:', res_quest.data_submissao.strftime('%d/%m/%Y %H:%M')])
    ws.append([])

    def adicionar_secao(titulo, dados):
        ws.append([titulo])
        ws.merge_cells(f'A{ws.max_row}:C{ws.max_row}')
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
        ws.cell(row=ws.max_row, column=1).fill = cinza_claro
        
        ws.append(['Escala/Item', 'Resultado', 'Referência'])
        for cell in ws[ws.max_row]:
            cell.fill = azul_somnus
            cell.font = fonte_branca

        for linha in dados:
            ws.append(linha)
        ws.append([])

    # Adicionando os Scores
    adicionar_secao("I. SAÚDE MENTAL", [
        ['DASS-21 Depressão', scores_dass['dass_depressao'], "0-21"],
        ['DASS-21 Ansiedade', scores_dass['dass_ansiedade'], "0-21"],
        ['DASS-21 Estresse',  scores_dass['dass_estresse'],  "0-21"],
        ['K10 Kessler',       scores_k10['k10_total'],       scores_k10['k10_classificacao']],
        ['SRQ-20 TMC',        scores_srq['srq_total'],       scores_srq['srq_status']],
    ])

    adicionar_secao("II. HÁBITOS E SONO", [
        ['ESE Epworth',       scores_ese['ese_total'],       scores_ese['ese_status']],
        ['AUDIT Álcool',      scores_audit['audit_total'],    scores_audit['audit_status']],
        ['PSQI Pittsburgh',   scores_psqi['psqi_global'],    scores_psqi['psqi_status']],
        ['IMC Atual',         imc,                           "kg/m²"],
    ])

    adicionar_secao("III. SUPORTE SOCIAL", [
        ['Família',           scores_emssp['suporte_familia'], "Máx: 28"],
        ['Amigos',            scores_emssp['suporte_amigos'],  "Máx: 28"],
        ['Outros',            scores_emssp['suporte_outros'],  "Máx: 28"],
        ['TOTAL',             scores_emssp['suporte_total'],   "Máx: 84"],
    ])

    # IV. Detalhamento
    ws.append(['IV. DETALHAMENTO DAS RESPOSTAS'])
    ws.append(['ID', 'Pergunta', 'Valor'])
    for cell in ws[ws.max_row]:
        cell.fill = azul_somnus
        cell.font = fonte_branca

    for rp in respostas_qs.order_by('pergunta__ordem'):
        valor = rp.alternativa.valor if rp.alternativa else rp.resposta_texto
        ws.append([rp.pergunta.identificador or f"ID_{rp.pergunta.id}", rp.pergunta.conteudo[:100], valor])

    # --- CORREÇÃO DO ERRO: AJUSTE DE LARGURA SEGURO ---
    for i, column_cells in enumerate(ws.columns, 1):
        max_length = 0
        column_letter = get_column_letter(i) # Pega a letra da coluna pelo índice (1=A, 2=B...)
        
        for cell in column_cells:
            try:
                if cell.value:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
            except:
                pass
        
        ws.column_dimensions[column_letter].width = min(max_length + 2, 60)

    # 5. RETORNO
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Somnus_Relatorio_{res_quest.id}.xlsx"'
    wb.save(response)
    return response