from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Adicionamos os campos personalizados da sua model
        fields = UserCreationForm.Meta.fields + (
            'email', 'first_name', 'last_name', 
            'sexo', 'cor_raca', 'estado_civil', 'data_nascimento'
        )
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'data_nascimento', 'sexo', 'cor_raca', 'estado_civil']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: Desabilitar o e-mail se você não quiser que ele mude a chave de login
        # self.fields['email'].disabled = True