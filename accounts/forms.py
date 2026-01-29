from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from datetime import date # Import necessário para a máscara de segurança

class UsuarioCreationForm(UserCreationForm):

    username = forms.CharField(
        label="Usuário",
        required=True,
        help_text="150 caracteres ou menos. Letras, números e @/./+/-/_ apenas."
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = UserCreationForm.Meta.fields + (
            'email', 'first_name', 'last_name', 
            'sexo', 'cor_raca', 'estado_civil', 'data_nascimento'
        )
        widgets = {
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d', # Formato ISO necessário para o navegador exibir o valor
                attrs={
                    'type': 'date',
                    'max': date.today().isoformat() # Impede seleção de datas futuras no calendário
                }
            ),
        }

class PerfilForm(forms.ModelForm):

    username = forms.CharField(label="Usuário", required=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'data_nascimento', 'sexo', 'cor_raca', 'estado_civil']
        widgets = {
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d', # FIX: Faz o navegador reconhecer a data salva no banco
                attrs={
                    'type': 'date', 
                    'class': 'form-control',
                    'max': date.today().isoformat() # Máscara de segurança: trava o calendário na data de hoje
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Validação de segurança no Backend (além da trava visual do HTML)
    def clean_data_nascimento(self):
        data_nasc = self.cleaned_data.get('data_nascimento')
        if data_nasc and data_nasc > date.today():
            raise forms.ValidationError("A data de nascimento não pode ser uma data futura.")
        return data_nasc