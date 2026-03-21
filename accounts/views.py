from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import PerfilForm
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
            
            # Adiciona ao grupo Assistente de Pesquisa automaticamente
            grupo, created = Group.objects.get_or_create(name='Assistente de Pesquisa')
            user.groups.add(grupo)
            
            messages.success(request, f'Assistente {user.first_name} cadastrado com sucesso!')
            return redirect('dashboard_respostas')
    else:
        form = CadastroAssistenteForm()
    
    return render(request, 'cadastrar_assistente.html', {'form': form})