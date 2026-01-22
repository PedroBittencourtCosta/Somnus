
from django.contrib import admin
from django.urls import include, path
from django.conf import settings

from core import views

admin.site.site_header = "Administração - Pesquisa TMC e Sono"
admin.site.site_title = "Portal de Dados CESM"
admin.site.index_title = "Bem-vindo ao Gerenciador da Pesquisa"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view, name="home"),
    path("accounts/", include("accounts.urls")),
    path("questionario/", include("core.urls")),
]

# if settings.DEBUG:
#     # Include django_browser_reload URLs only in DEBUG mode
#     urlpatterns += [
#         path("__reload__/", include("django_browser_reload.urls")),
#     ]
