from django.contrib import admin
from .models import TCLE, AceiteTCLE

@admin.register(TCLE)
class TCLEAdmin(admin.ModelAdmin):
    list_display = ('versao', 'data_criacao')

@admin.register(AceiteTCLE)
class AceiteTCLEAdmin(admin.ModelAdmin):
    list_display = ('resposta_questionario', 'tcle', 'data_aceite')
    readonly_fields = ('data_aceite',) # Evita alteração manual da data de aceite
