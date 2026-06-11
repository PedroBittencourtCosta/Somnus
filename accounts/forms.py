from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
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
    ROLE_CHOICES = [
        ('Assistente de Pesquisa', 'Assistente de Pesquisa (Coleta de Dados)'),
        ('Pesquisador', 'Pesquisador (Gestão Completa)'),
    ]
    papel = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select rounded-3'})
    )
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


class AlterarSenhaForm(PasswordChangeForm):
    """
    Wrapper do PasswordChangeForm do Django.
    Valida a senha atual e exige confirmação da nova — padrão idêntico
    ao fluxo de recuperação de senha (PasswordResetConfirmView).
    """
    old_password = forms.CharField(
        label="Senha atual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Digite sua senha atual',
            'id': 'id_old_password',
        }),
    )
    new_password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Digite a nova senha',
            'id': 'id_new_password1',
        }),
    )
    new_password2 = forms.CharField(
        label="Confirmar nova senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Confirme a nova senha',
            'id': 'id_new_password2',
        }),
    )