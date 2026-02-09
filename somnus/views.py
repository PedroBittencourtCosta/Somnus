

from django.shortcuts import render


def sobre_nos(request):
    return render(request, 'sobre_nos.html')

def sono(request):
    return render(request, 'sono.html')

def bem_estar(request):
    return render(request, 'bem_estar.html')

def dicas(request):
    return render(request, 'dicas_seg.html')