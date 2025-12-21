
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    # Opções para Cor/Raça [cite: 639]
    COR_RACA_CHOICES = [
        ('1', 'Branco'),
        ('2', 'Preta'),
        ('3', 'Parda'),
        ('4', 'Amarela'),
        ('5', 'Indígena'),
    ]

    # Opções para Estado Civil [cite: 639]
    ESTADO_CIVIL_CHOICES = [
        ('1', 'Solteiro(a)'),
        ('2', 'Casado(a)'),
        ('3', 'Com companheiro(a)'),
        ('4', 'Viúvo(a)'),
        ('5', 'Outro'),
    ]

    SEXO_CHOICES = [('F', 'Feminino'), ('M', 'Masculino')]

    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    cor_raca = models.CharField(max_length=1, choices=COR_RACA_CHOICES) # [cite: 639]
    estado_civil = models.CharField(max_length=1, choices=ESTADO_CIVIL_CHOICES) # [cite: 639]
    data_nascimento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username