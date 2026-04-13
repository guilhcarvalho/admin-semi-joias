from django.db import models

class ClienteQuerySet(models.QuerySet):
    def param_filter(self, nome=None, celular=None):
        queryset = self
        if nome:
            queryset = queryset.filter(first_name__icontains=nome)
        if celular:
            queryset = queryset.filter(phone_number__icontains=celular)
        return queryset