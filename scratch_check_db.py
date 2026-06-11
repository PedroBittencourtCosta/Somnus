import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'somnus.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'core_respostaquestionario'")
    print("core_respostaquestionario:", cursor.fetchall())
    
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'core_respostapergunta'")
    print("core_respostapergunta:", cursor.fetchall())
