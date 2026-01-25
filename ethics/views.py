from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from ethics.models import TCLE, AceiteTCLE
# Create your views here.
@login_required
def aceitar_tcle(request, tcle_id):
    if request.method == 'POST':
        tcle = get_object_or_404(TCLE, id=tcle_id)
        AceiteTCLE.objects.get_or_create(usuario=request.user, tcle=tcle)
        return redirect(request.META.get('HTTP_REFERER', 'home'))