from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from datetime import date

class UsuarioCreationForm(UserCreationForm):
    # Definimos email como obrigatório no formulário
    email = forms.EmailField(label="E-mail", required=True)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Removido 'username' da lista de campos visíveis
        fields = (
            'email', 'first_name', 'last_name', 
            'sexo', 'cor_raca', 'estado_civil', 'data_nascimento'
        )
        widgets = {
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'max': date.today().isoformat()
                }
            ),
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # Removido 'username' para evitar conflitos na edição
        fields = ['first_name', 'last_name', 'email', 'data_nascimento', 'sexo', 'cor_raca', 'estado_civil']
        widgets = {
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date', 
                    'class': 'form-control',
                    'max': date.today().isoformat()
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_data_nascimento(self):
        data_nasc = self.cleaned_data.get('data_nascimento')
        if data_nasc and data_nasc > date.today():
            raise forms.ValidationError("A data de nascimento não pode ser uma data futura.")
        return data_nasc