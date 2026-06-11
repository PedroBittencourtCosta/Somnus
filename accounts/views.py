from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from .forms import PerfilForm, AlterarSenhaForm
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.forms import UsuarioCreationForm
from django.contrib.auth.models import Group
from .forms import CadastroAssistenteForm

def login_view(request):
    # 1. Se já estiver logado, não precisa ver o login
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email_login = request.POST.get('email')
        senha_login = request.POST.get('password')

        user = authenticate(request, username=email_login, password=senha_login)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            from django.contrib.auth import get_user_model
            Usuario = get_user_model()
            try:
                u = Usuario.objects.get(email=email_login)
                if not u.is_active:
                    messages.error(request, "Sua conta está desativada. Entre em contato com um pesquisador.", extra_tags='login_modal')
                else:
                    messages.error(request, "E-mail ou senha inválidos.", extra_tags='login_modal')
            except Usuario.DoesNotExist:
                messages.error(request, "E-mail ou senha inválidos.", extra_tags='login_modal')
            
            # Redireciona para a mesma página onde o usuário tentou logar
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # 2. Caso o usuário acesse via barra de endereços (GET)
    # Enviamos uma mensagem informativa para disparar o JavaScript do modal
    messages.info(request, "abrir_modal")
    return redirect('home')

def logout_view(request):
    logout(request)
    return redirect('home')

def cadastro_view(request):
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça login para continuar.')
            # messages.info(request, 'abrir_modal') 
            return redirect('home')
    else:
        form = UsuarioCreationForm()
    
    return render(request, 'cadastro.html', {'form': form})

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Seus dados foram atualizados com sucesso!")
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'perfil.html', {'form': form})


@login_required
def alterar_senha_view(request):
    if request.method == 'POST':
        form = AlterarSenhaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantém a sessão ativa após a troca (padrão Django)
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso!")
            return redirect('perfil')
    else:
        form = AlterarSenhaForm(request.user)
    return render(request, 'password/alterar_senha.html', {'form': form})


# Função para verificar se é Pesquisador (Segurança)
def eh_pesquisador(user):
    return user.is_staff or user.groups.filter(name='Pesquisador').exists()

@login_required
@user_passes_test(eh_pesquisador)
def cadastrar_assistente(request):
    if request.method == 'POST':
        form = CadastroAssistenteForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['senha']) # Criptografa a senha
            user.save()
            
            papel = form.cleaned_data.get('papel', 'Assistente de Pesquisa')
            
            # Adiciona ao grupo escolhido (Pesquisador ou Assistente)
            grupo, created = Group.objects.get_or_create(name=papel.split(' (')[0])
            user.groups.add(grupo)
            
            messages.success(request, f'Colaborador {user.first_name} cadastrado com sucesso como {papel.split(" (")[0]}!')
            return redirect('gestao_assistentes')
    else:
        form = CadastroAssistenteForm()
    return render(request, 'cadastrar_assistente.html', {'form': form})

@login_required
@user_passes_test(eh_pesquisador)
def gestao_assistentes(request):
    from accounts.models import Usuario
    usuarios = Usuario.objects.exclude(id=request.user.id).exclude(is_superuser=True).prefetch_related('groups').order_by('first_name')
    return render(request, 'gestao_assistentes.html', {'usuarios': usuarios})

@login_required
@user_passes_test(eh_pesquisador)
def alternar_status_assistente(request, usuario_id):
    from accounts.models import Usuario
    from django.http import JsonResponse
    from django.views.decorators.http import require_POST

    try:
        usuario = Usuario.objects.get(id=usuario_id)
        if usuario != request.user:
            usuario.is_active = not usuario.is_active
            usuario.save()
            status_label = "reativado" if usuario.is_active else "desativado"

            # Resposta JSON para requisições fetch (AJAX)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({
                    'status': 'success',
                    'is_active': usuario.is_active,
                    'message': f'O acesso de {usuario.first_name} foi {status_label} com sucesso.'
                })

            messages.success(request, f'O acesso de {usuario.first_name} foi {status_label} com sucesso.')
        else:
            if 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Você não pode alterar seu próprio acesso.'}, status=403)
    except Usuario.DoesNotExist:
        if 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado.'}, status=404)
        messages.error(request, "Usuário não encontrado.")

    return redirect('gestao_assistentes')