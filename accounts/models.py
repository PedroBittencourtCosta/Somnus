from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    COR_RACA_CHOICES = [
        ('1', 'Branco'),
        ('2', 'Preta'),
        ('3', 'Parda'),
        ('4', 'Amarela'),
        ('5', 'Indígena'),
    ]

    ESTADO_CIVIL_CHOICES = [
        ('1', 'Solteiro(a)'),
        ('2', 'Casado(a)'),
        ('3', 'Com companheiro(a)'),
        ('4', 'Viúvo(a)'),
        ('5', 'Outro'),
    ]

    SEXO_CHOICES = [('F', 'Feminino'), ('M', 'Masculino')]

    email = models.EmailField('E-mail', unique=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    cor_raca = models.CharField(max_length=1, choices=COR_RACA_CHOICES)
    estado_civil = models.CharField(max_length=1, choices=ESTADO_CIVIL_CHOICES)
    data_nascimento = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # O username será preenchido automaticamente, não precisa ser requerido

    def save(self, *args, **kwargs):
        # Sincronização automática: o username recebe o valor do email
        if self.email:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.email