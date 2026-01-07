from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    # 1. Se o usuário já estiver logado, ele é enviado para a home
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email_login = request.POST.get('email')
        senha_login = request.POST.get('password')

        # O authenticate utiliza o e-mail como username se o seu model estiver configurado assim
        user = authenticate(request, username=email_login, password=senha_login)

        if user is not None:
            login(request, user)
            # Login bem-sucedido: vai para a home do Somnus
            return redirect('home')
        else:
            # Erro de credenciais: exibe mensagem e permanece na página de login
            messages.error(request, "E-mail ou senha inválidos.")
            return render(request, 'login.html')
    
    # 2. Caso o acesso seja via GET (usuário entrou na URL /login/)
    # Agora apenas renderizamos a nova página independente
    return render(request, 'login.html')

def logout_view(request):
    # Encerra a sessão e manda para a home (onde o usuário verá o botão 'Entrar' novamente)
    logout(request)
    return redirect('home')