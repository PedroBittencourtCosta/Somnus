# accounts/migrations/000X_create_groups.py
from django.db import migrations

def create_medicos_group(apps, schema_editor):
    # Buscamos o modelo de Grupo de forma segura dentro da migração
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    
    # Criamos o grupo se ele não existir
    group, created = Group.objects.get_or_create(name='Medicos')
    
    # Opcional: Você pode adicionar permissões específicas aqui no futuro
    # Ex: permissao = Permission.objects.get(codename='can_view_results')
    # group.permissions.add(permissao)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'), # Certifique-se que depende da migração inicial
    ]

    operations = [
        migrations.RunPython(create_medicos_group),
    ]