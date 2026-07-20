import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'somnus.settings')
django.setup()

from core.models import EscalaConfig

for e in EscalaConfig.objects.all():
    print(e.nome)
    if e.config_dinamica:
        classificacoes = e.config_dinamica.get('classificacoes', [])
        for c in classificacoes:
            print("  ", c.get('nome', ''))
    else:
        print("   Nenhuma (não dinâmico)")
