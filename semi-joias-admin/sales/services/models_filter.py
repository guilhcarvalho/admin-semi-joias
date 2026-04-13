from django.db import models

class MaletaQuerySet(models.QuerySet):
    def param_filter(self, month=None, order_number=None):
        queryset = self
        if month:
            queryset = queryset.filter(month__icontains=month)
        if order_number:
            queryset = queryset.filter(order_number__icontains=order_number)
        return queryset
    
class ProdutosQuerySet(models.QuerySet):
    def param_filter(self, product_briefcase=None, product_name=None, product_code=None):
        queryset = self
        if product_briefcase:
            queryset = queryset.filter(product_briefcase__icontains=product_briefcase)
        if product_name:
            queryset = queryset.filter(product_name__icontains=product_name)
        if product_code:
            queryset = queryset.filter(product_code__icontains=product_code)
            
        return queryset