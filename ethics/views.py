from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from core.models import RespostaQuestionario
from .models import TCLE, AceiteTCLE, RevogacaoConsentimento


@login_required
def aceitar_tcle(request, tcle_id):
    if request.method == 'POST':
        # 1. Apenas marcamos na sessão que o TCLE foi aceito para este atendimento
        request.session['tcle_aceito'] = True
        request.session.modified = True

        # 2. Redirecionamos de volta para o questionário
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    return redirect('home')


@login_required
def lista_tcle(request):
    """Lista todas as versões de TCLE, da mais recente para a mais antiga."""
    if not (request.user.is_staff or _is_pesquisador(request.user)):
        messages.error(request, 'Acesso restrito a pesquisadores.')
        return redirect('home')

    tcles = TCLE.objects.all().order_by('-data_criacao')
    return render(request, 'lista_tcle.html', {'tcles': tcles})


@login_required
def nova_versao_tcle(request):
    """Cria uma nova versão de TCLE."""
    if not (request.user.is_staff or _is_pesquisador(request.user)):
        messages.error(request, 'Acesso restrito a pesquisadores.')
        return redirect('home')

    if request.method == 'POST':
        conteudo = request.POST.get('conteudo', '').strip()
        versao_str = request.POST.get('versao', '').strip()

        erros = []
        if not conteudo:
            erros.append('O conteúdo do TCLE não pode estar em branco.')
        if not versao_str:
            erros.append('A versão é obrigatória.')
        else:
            try:
                versao = float(versao_str.replace(',', '.'))
                if versao <= 0:
                    erros.append('A versão deve ser um número positivo.')
                elif TCLE.objects.filter(versao=versao).exists():
                    erros.append(f'Já existe um TCLE com a versão {versao}.')
            except ValueError:
                erros.append('Versão inválida. Use um número como 1.0 ou 2.5.')

        if erros:
            for erro in erros:
                messages.error(request, erro)
            return render(request, 'nova_versao_tcle.html', {
                'conteudo': conteudo,
                'versao': versao_str,
            })

        TCLE.objects.create(conteudo=conteudo, versao=versao)
        messages.success(request, f'TCLE versão {versao} criado com sucesso!')
        return redirect('lista_tcle')

    # Sugere automaticamente a próxima versão
    ultimo = TCLE.objects.order_by('-versao').first()
    proxima_versao = round((ultimo.versao + 1.0) if ultimo else 1.0, 1)

    return render(request, 'nova_versao_tcle.html', {
        'versao': proxima_versao,
    })


@login_required
def revogar_consentimento(request):
    """
    RF-014: localiza a coleta pelo código do participante e a exclui de forma
    definitiva (respostas, resultados de escalas e aceite saem em cascata).
    """
    if not (request.user.is_staff or _is_pesquisador(request.user)):
        messages.error(request, 'Acesso restrito a pesquisadores.')
        return redirect('home')

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        resposta = RespostaQuestionario.objects.filter(codigo_paciente=codigo).select_related('questionario').first()
        if not resposta:
            messages.error(request, 'Nenhuma coleta encontrada com esse código. Ela pode já ter sido excluída.')
            return redirect('revogar_consentimento')

        aceite = AceiteTCLE.objects.filter(resposta_questionario=resposta).select_related('tcle').first()
        with transaction.atomic():
            RevogacaoConsentimento.objects.create(
                codigo_paciente=resposta.codigo_paciente,
                questionario_titulo=resposta.questionario.titulo,
                tcle_versao=aceite.tcle.versao if aceite else None,
                data_coleta=resposta.data_submissao,
                revogado_por=request.user,
            )
            resposta.delete()

        messages.success(request, f'Consentimento revogado. Os dados da coleta {codigo} foram excluídos definitivamente.')
        return redirect('revogar_consentimento')

    codigo = request.GET.get('codigo', '').strip().upper()
    resposta = None
    aceite = None
    if codigo:
        resposta = (
            RespostaQuestionario.objects
            .filter(codigo_paciente=codigo)
            .select_related('questionario', 'pesquisadora')
            .first()
        )
        if resposta:
            aceite = AceiteTCLE.objects.filter(resposta_questionario=resposta).select_related('tcle').first()

    paginator = Paginator(RevogacaoConsentimento.objects.select_related('revogado_por'), 10)
    revogacoes = paginator.get_page(request.GET.get('page'))

    return render(request, 'revogar_consentimento.html', {
        'codigo': codigo,
        'resposta': resposta,
        'aceite': aceite,
        'total_respostas': resposta.respostas.count() if resposta else 0,
        'revogacoes': revogacoes,
    })


# ── Helper ────────────────────────────────────────────────────────────────────
def _is_pesquisador(user):
    """Verifica se o usuário pertence ao grupo Pesquisador."""
    return user.groups.filter(name='Pesquisador').exists()