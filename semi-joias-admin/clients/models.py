from django.db import models
from .validator import name_validator, phone_validator
from clients.services.models_filter import ClienteQuerySet

class Cliente(models.Model):
    first_name = models.CharField(max_length=20, validators=[name_validator], blank=False, verbose_name="primeiro nome")
    last_name = models.CharField(max_length=30, validators=[name_validator], blank=False, verbose_name="sobrenome")
    phone_number = models.CharField(max_length=11, validators=[phone_validator], blank=False, verbose_name="número de telefone")
    objects = ClienteQuerySet.as_manager()
    
    def save(self, *args, **kwargs):
        self.first_name = self.first_name.title()
        self.last_name = self.last_name.title()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = 'clientes'
        
    @property
    def formatted_phone(self):
        phone = self.phone_number
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return self.full_name