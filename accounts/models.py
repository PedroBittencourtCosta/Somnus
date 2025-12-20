
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
 
    SEXO_CHOICES = [('F', 'Feminino'), ('M', 'Masculino')]
    
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    cor_raca = models.CharField(max_length=20) 
    estado_civil = models.CharField(max_length=30) 
    data_nascimento = models.DateField(null=True, blank=True) 

    def __str__(self):
        return self.username