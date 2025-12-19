
from django.contrib import admin
from django.urls import include, path
from django.conf import settings

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
