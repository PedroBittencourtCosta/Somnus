from django.http import HttpRequest
from django.shortcuts import render

# Create your views here.

def index_view(request: HttpRequest):
    return render(request, 'home.html')