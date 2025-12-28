from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redireciona se já estiver logado

    if request.method == 'POST':
        email_login = request.POST.get('email')
        senha_login = request.POST.get('password')

        # O Django usará o e-mail aqui por causa do USERNAME_FIELD
        user = authenticate(request, username=email_login, password=senha_login)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "E-mail ou senha inválidos.")
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
