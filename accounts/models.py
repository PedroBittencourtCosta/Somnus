from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):

    email = models.EmailField('E-mail', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # O username será preenchido automaticamente, não precisa ser requerido

    def save(self, *args, **kwargs):
        # Sincronização automática: o username recebe o valor do email
        if self.email:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.email