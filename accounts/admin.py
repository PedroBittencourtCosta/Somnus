# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario
from .forms import UsuarioCreationForm  # Importe o formulário que criamos acima

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Vinculamos o formulário customizado para a criação
    add_form = UsuarioCreationForm
    
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('-date_joined',)

    # 1. Formulário de EDIÇÃO (campos que aparecem ao clicar em um usuário existente)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    # 2. Formulário de CRIAÇÃO (campos que aparecem na tela de "Adicionar Usuário")
    # Sobrescrevemos totalmente para evitar as abas duplicadas
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'password_confirmation'),
        }),
    )

    # Mantemos o label amigável para o e-mail
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'username' in form.base_fields:
            form.base_fields['username'].label = "E-mail (Login)"
        return form