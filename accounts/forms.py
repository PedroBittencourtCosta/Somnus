from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from datetime import date
from django.contrib.auth.models import Group

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

class CadastroAssistenteForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))
    confirmar_senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}))

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'E-mail institucional'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha != confirmar_senha:
            raise forms.ValidationError("As senhas não conferem.")
        return cleaned_data