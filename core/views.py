
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from core.Scaleprocessor import EscalaEngine, SafeParser

from ethics.models import TCLE, AceiteTCLE
from .models import Questionario, Secao, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta, EscalaConfig
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

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
    
    # Coleta assistida: permite múltiplas submissões pelo pesquisador/assistente.
    # Ocultamos a lógica de "já respondido".
    return render(request, 'lista_questionarios.html', {
        'questionarios': questionarios,
        'respondidos': []
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

    # 3. PROCESSAMENTO DAS ESCALAS VINCULADAS
    escalas_resultados = []
    for escala in res_quest.questionario.escalas_config.all():
        resultado = EscalaEngine.processar(answers_map, escala)
        if "erro" not in resultado:
            chaves_valor = []
            chaves_status = {}
            
            for k, v in resultado.items():
                k_str = str(k)
                if k_str.endswith('_status') or k_str == 'status' or k_str.endswith('_classificacao') or k_str == 'classificacao':
                    prefix = k_str.replace('_status', '').replace('status', '').replace('_classificacao', '').replace('classificacao', '')
                    chaves_status[prefix] = v
                elif isinstance(v, (int, float, str)) and not isinstance(v, list):
                    chaves_valor.append((k_str, v))
            
            for k, v in chaves_valor:
                prefix = k.replace('_total', '').replace('_global', '').replace('_valor', '')
                
                referencia = "-"
                if prefix in chaves_status:
                    referencia = chaves_status.pop(prefix)
                elif k in chaves_status:
                    referencia = chaves_status.pop(k)
                elif "" in chaves_status:
                    referencia = chaves_status.pop("")
                    
                key_formatted = k.replace('_', ' ').title()
                escalas_resultados.append([f"{escala.nome} - {key_formatted}", v, str(referencia)])
                
            for pref, ref in chaves_status.items():
                nome_formatado = f"{escala.nome} - Status {pref.replace('_', ' ').title()}".strip()
                if nome_formatado.endswith('- Status'):
                    nome_formatado = f"{escala.nome} - Status"
                escalas_resultados.append([nome_formatado, "-", str(ref)])
    
    # IMC Fallback (caso ainda queiram sem precisar configurar)
    peso = SafeParser.to_float(answers_map.get('peso', 0))
    altura = SafeParser.to_float(answers_map.get('altura', 0))
    if altura > 0:
        imc = round(peso / (altura ** 2), 2)
        escalas_resultados.append(["IMC Calculado Automaticamente", imc, "kg/m²"])

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
        if not dados: return
        ws.append([titulo])
        ws.merge_cells(f'A{ws.max_row}:C{ws.max_row}')
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
        ws.cell(row=ws.max_row, column=1).fill = cinza_claro
        
        ws.append(['Escala/Métrica', 'Resultado', 'Referência'])
        for cell in ws[ws.max_row]:
            cell.fill = azul_somnus
            cell.font = fonte_branca

        for linha in dados:
            ws.append(linha)
        ws.append([])

    # Adicionando os Scores Calculados Dinamicamente
    adicionar_secao("I. RESULTADOS DAS ESCALAS", escalas_resultados)

    # II. Detalhamento
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

@login_required
def editar_questionario_view(request, pk=None):
    questionario_json = "{}"
    questionario = None
    
    if pk:
        questionario = get_object_or_404(Questionario, pk=pk)
        dados = {
            "id": questionario.id,
            "titulo": questionario.titulo,
            "descricao": questionario.descricao,
            "secoes": []
        }
        for secao in questionario.secoes.all().order_by('ordem'):
            sec_data = {
                "id": secao.id,
                "titulo": secao.titulo,
                "instrucao": secao.instrucao,
                "layout": secao.layout,
                "ordem": secao.ordem,
                "perguntas": []
            }
            for perg in secao.perguntas.all().order_by('ordem'):
                perg_data = {
                    "id": perg.id,
                    "conteudo": perg.conteudo,
                    "tipo": perg.tipo,
                    "mascara": perg.mascara,
                    "config_mista": perg.config_mista,
                    "obrigatoria": perg.obrigatoria,
                    "identificador": perg.identificador,
                    "ordem": perg.ordem,
                    "alternativas": []
                }
                for alt in perg.alternativas.all():
                    perg_data["alternativas"].append({
                        "id": alt.id,
                        "conteudo": alt.conteudo,
                        "valor": alt.valor
                    })
                sec_data["perguntas"].append(perg_data)
            dados["secoes"].append(sec_data)
        questionario_json = json.dumps(dados)

    return render(request, 'criar_questionario.html', {
        'questionario': questionario,
        'questionario_json': questionario_json
    })

@login_required
@require_POST
def salvar_questionario_api(request):
    try:
        data = json.loads(request.body)
        questionario_id = data.get('id')
        
        with transaction.atomic():
            if questionario_id:
                quest = Questionario.objects.get(pk=questionario_id)
                quest.titulo = data.get('titulo', '')
                quest.descricao = data.get('descricao', '')
                quest.save()
            else:
                quest = Questionario.objects.create(
                    titulo=data.get('titulo', ''),
                    descricao=data.get('descricao', '')
                )
            
            secoes_ids = []
            perguntas_ids = []
            alternativas_ids = []
            
            for index_secao, sec_data in enumerate(data.get('secoes', [])):
                sec_id = sec_data.get('id')
                if sec_id and str(sec_id).isdigit():
                    secao = Secao.objects.get(pk=sec_id, questionario=quest)
                    secao.titulo = sec_data.get('titulo', '')
                    secao.instrucao = sec_data.get('instrucao', '')
                    secao.layout = sec_data.get('layout', 'LISTA')
                    secao.ordem = index_secao + 1
                    secao.save()
                else:
                    secao = Secao.objects.create(
                        questionario=quest,
                        titulo=sec_data.get('titulo', ''),
                        instrucao=sec_data.get('instrucao', ''),
                        layout=sec_data.get('layout', 'LISTA'),
                        ordem=index_secao + 1
                    )
                secoes_ids.append(secao.id)
                
                for index_perg, perg_data in enumerate(sec_data.get('perguntas', [])):
                    perg_id = perg_data.get('id')
                    if perg_id and str(perg_id).isdigit():
                        perg = Pergunta.objects.get(pk=perg_id, secao=secao)
                        perg.conteudo = perg_data.get('conteudo', '')
                        perg.tipo = perg_data.get('tipo', 'MC')
                        perg.mascara = perg_data.get('mascara', 'NENHUMA')
                        perg.config_mista = perg_data.get('config_mista', 'QUALQUER')
                        perg.obrigatoria = perg_data.get('obrigatoria', True)
                        perg.identificador = perg_data.get('identificador', '')
                        perg.ordem = index_perg + 1
                        perg.save()
                    else:
                        perg = Pergunta.objects.create(
                            secao=secao,
                            conteudo=perg_data.get('conteudo', ''),
                            tipo=perg_data.get('tipo', 'MC'),
                            mascara=perg_data.get('mascara', 'NENHUMA'),
                            config_mista=perg_data.get('config_mista', 'QUALQUER'),
                            obrigatoria=perg_data.get('obrigatoria', True),
                            identificador=perg_data.get('identificador', ''),
                            ordem=index_perg + 1
                        )
                    perguntas_ids.append(perg.id)
                    
                    for index_alt, alt_data in enumerate(perg_data.get('alternativas', [])):
                        alt_id = alt_data.get('id')
                        try:
                            valor_int = int(alt_data.get('valor', 0))
                        except ValueError:
                            valor_int = 0
                            
                        if alt_id and str(alt_id).isdigit():
                            alt = Alternativa.objects.get(pk=alt_id, pergunta=perg)
                            alt.conteudo = alt_data.get('conteudo', '')
                            alt.valor = valor_int
                            alt.save()
                        else:
                            alt = Alternativa.objects.create(
                                pergunta=perg,
                                conteudo=alt_data.get('conteudo', ''),
                                valor=valor_int
                            )
                        alternativas_ids.append(alt.id)
            
            Alternativa.objects.filter(pergunta__secao__questionario=quest).exclude(id__in=alternativas_ids).delete()
            Pergunta.objects.filter(secao__questionario=quest).exclude(id__in=perguntas_ids).delete()
            Secao.objects.filter(questionario=quest).exclude(id__in=secoes_ids).delete()
            
        return JsonResponse({'status': 'success', 'questionario_id': quest.id})
        
    except Exception as e:
        import traceback
        return JsonResponse({'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}, status=400)

@login_required
def configurar_escala_view(request, pk):
    questionario = get_object_or_404(Questionario, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            acao = data.get('acao')
            escala_id = data.get('escala_id')
            
            if acao == 'vincular':
                escala = get_object_or_404(EscalaConfig, id=escala_id)
                escala.questionarios.add(questionario)
                return JsonResponse({'status': 'success', 'escala_id': escala.id, 'nome': escala.nome})
            elif acao == 'desvincular':
                escala = get_object_or_404(EscalaConfig, id=escala_id)
                escala.questionarios.remove(questionario)
                return JsonResponse({'status': 'success', 'escala_id': escala.id, 'nome': escala.nome})
            
            nome = data.get('nome', f'Escala para {questionario.titulo}'[:100])
            
            if escala_id:
                # Editar escala existente
                config = get_object_or_404(EscalaConfig, id=escala_id)
                config.nome = nome
            else:
                # Criar nova escala
                config = EscalaConfig.objects.create(nome=nome)
                config.questionarios.add(questionario)
                
            config.strategy_class = data.get('strategy_class', 'DYNAMIC')
            if config.strategy_class == 'DYNAMIC':
                config.config_dinamica = data.get('config_dinamica', {})
            else:
                config.config_dinamica = None
                
            config.save()
            return JsonResponse({'status': 'success', 'escala_id': config.id, 'nome': config.nome})
        except Exception as e:
            import traceback
            return JsonResponse({'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}, status=400)
            
    # Coleta todas as perguntas que possuem um identificador (variáveis)
    perguntas_com_id = Pergunta.objects.filter(
        secao__questionario=questionario
    ).exclude(identificador__exact='').exclude(identificador__isnull=True).values('id', 'identificador', 'conteudo')
    
    # Coleta configurações de todas as escalas cadastradas
    escalas_cadastradas = EscalaConfig.objects.all().prefetch_related('questionarios')
    escalas_templates = []
    for e in escalas_cadastradas:
        is_linked = e.questionarios.filter(id=questionario.id).exists()
        escalas_templates.append({
            'id': e.id,
            'nome': e.nome,
            'strategy_class': e.strategy_class,
            'is_linked': is_linked,
            'config': e.config_dinamica or {}
        })
    
    context = {
        'questionario': questionario,
        'config_json': '{}',
        'perguntas_json': json.dumps(list(perguntas_com_id)),
        'escalas_templates_json': json.dumps(escalas_templates)
    }
    return render(request, 'configurar_escala.html', context)