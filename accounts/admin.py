from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    # Adiciona seus campos customizados nas telas de edição do Admin
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Epidemiológicas', {'fields': ('sexo', 'cor_raca', 'estado_civil', 'data_nascimento')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Epidemiológicas', {'fields': ('sexo', 'cor_raca', 'estado_civil', 'data_nascimento')}),
    )

admin.site.register(Usuario, UsuarioAdmin)
