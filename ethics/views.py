from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TCLE


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


# ── Helper ────────────────────────────────────────────────────────────────────
def _is_pesquisador(user):
    """Verifica se o usuário pertence ao grupo Pesquisador."""
    return user.groups.filter(name='Pesquisador').exists()