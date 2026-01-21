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