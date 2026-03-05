from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from datetime import date

class UsuarioCreationForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Mantemos apenas o que a pesquisadora precisa informar no cadastro
        fields = ('email', 'first_name', 'last_name')

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # Perfil agora é apenas para dados de contato/nome da aluna
        fields = ['first_name', 'last_name', 'email']