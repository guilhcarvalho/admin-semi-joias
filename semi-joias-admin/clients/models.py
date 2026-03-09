from django.db import models


class Clientes(models.Model):
    first_name = models.CharField(max_length=20, verbose_name="primeiro nome")
    last_name = models.CharField(max_length=30, verbose_name="sobrenome")
    phone_number = models.CharField(max_length=11, verbose_name="número de telefone")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    