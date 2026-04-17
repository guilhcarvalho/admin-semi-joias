from django.db import models
from django.db.models.functions import Concat
from django.db.models import Value


class ClienteQuerySet(models.QuerySet):
    def param_filter(self, nome=None, celular=None):
        queryset = self
        if nome:
                queryset = queryset.annotate(full_name_f=Concat(
                'first_name',
                Value(' '),
                'last_name'
                )).filter(full_name_f__icontains=nome)
                
        if celular:
            queryset = queryset.filter(phone_number__icontains=celular)
            
        return queryset