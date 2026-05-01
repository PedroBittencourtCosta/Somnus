from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def aceitar_tcle(request, tcle_id):
    if request.method == 'POST':
        # 1. Apenas marcamos na sessão que o TCLE foi aceito para este atendimento
        request.session['tcle_aceito'] = True
        request.session.modified = True
        
        # 2. Redirecionamos de volta para o questionário
        # request.META.get('HTTP_REFERER') volta para a página anterior (o form)
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    return redirect('home')