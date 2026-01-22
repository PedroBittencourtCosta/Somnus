from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Questionario, Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta

def index_view(request: HttpRequest):
    return render(request, 'home.html')

@login_required
def responder_questionario(request, pk):
    # Carregamos o questionário e todas as suas seções, perguntas e alternativas de uma vez
    questionario = get_object_or_404(
        Questionario.objects.prefetch_related('secoes__perguntas__alternativas'), 
        pk=pk
    )
    
    secoes = questionario.secoes.all()

    if request.method == 'POST':
        res_quest = RespostaQuestionario.objects.create(
            usuario=request.user,
            questionario=questionario
        )
        
        # Iteramos por todas as perguntas enviadas no POST
        for key, value in request.POST.items():
            if key.startswith('pergunta_'):
                pergunta_id = key.replace('pergunta_', '')
                pergunta = Pergunta.objects.get(id=pergunta_id)
                
                if pergunta.tipo == 'MC':
                    alternativa = Alternativa.objects.get(id=value)
                    RespostaPergunta.objects.create(
                        resposta_questionario=res_quest,
                        pergunta=pergunta,
                        alternativa=alternativa
                    )
                else:
                    RespostaPergunta.objects.create(
                        resposta_questionario=res_quest,
                        pergunta=pergunta,
                        resposta_texto=value
                    )
        
        messages.success(request, "Questionário enviado com sucesso!")
        return redirect('home')

    return render(request, 'responder_questionario.html', {
        'questionario': questionario,
        'secoes': secoes
    })

def lista_questionarios(request):
    # Busca todos os questionários cadastrados
    questionarios = Questionario.objects.all().order_by('-data_criacao')
    return render(request, 'lista_questionarios.html', {'questionarios': questionarios})