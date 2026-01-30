from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    list_display = ('first_name', 'last_name','email', 'sexo', 'cor_raca', 'data_nascimento', 'is_staff')
    search_fields = ('first_name', 'last_name', 'email', 'first_name', 'last_name')
    list_filter = ('sexo', 'cor_raca', 'is_staff', 'is_superuser')
    ordering = ('-date_joined',)

    # Configuração para o formulário de EDIÇÃO
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Epidemiológicas', {
            'fields': ('sexo', 'cor_raca', 'estado_civil', 'data_nascimento')
        }),
    )

    # Configuração para o formulário de CRIAÇÃO (Novo Usuário)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Epidemiológicas', {
            'fields': ('sexo', 'cor_raca', 'estado_civil', 'data_nascimento'),
        }),
    )

admin.site.register(Usuario, UsuarioAdmin)