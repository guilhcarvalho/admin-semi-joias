from django.db import models


class PAYMENT_METHODS(models.TextChoices):
    PIX      = 'pix',      'Pix'
    DEBITO   = 'debito',   'Débito'
    CREDITO  = 'credito',  'Crédito'
    DINHEIRO = 'dinheiro', 'Dinheiro'


class PAYMENT_SITUATION(models.TextChoices):
    ADIMPLENTE   = 'adimplente',   'Adimplente'
    INADIMPLENTE = 'inadimplente', 'Inadimplente'


class MONTH_SELECTION(models.TextChoices):
    JANEIRO   = 'janeiro',   'Janeiro'
    FEVEREIRO = 'fevereiro', 'Fevereiro'
    MARCO     = 'março',     'Março'
    ABRIL     = 'abril',     'Abril'
    MAIO      = 'maio',      'Maio'
    JUNHO     = 'junho',     'Junho'
    JULHO     = 'julho',     'Julho'
    AGOSTO    = 'agosto',    'Agosto'
    SETEMBRO  = 'setembro',  'Setembro'
    OUTUBRO   = 'outubro',   'Outubro'
    NOVEMBRO  = 'novembro',  'Novembro'
    DEZEMBRO  = 'dezembro',  'Dezembro'


class SALE_STATUS(models.TextChoices):
    ATIVA             = 'ativa',             'Ativa'
    CANCELADA         = 'cancelada',         'Cancelada'
    DEVOLVIDA_PARCIAL = 'devolvida_parcial', 'Devolução Parcial'


class GARANTIA_STATUS(models.TextChoices):
    ENVIADO    = 'enviado',    'Enviado'
    EM_ANALISE = 'em_analise', 'Em Análise'
    RESOLVIDO  = 'resolvido',  'Resolvido'
    RECUSADO   = 'recusado',   'Recusado'


class PARCELA_SITUACAO(models.TextChoices):
    PENDENTE  = 'pendente',  'Pendente'
    PAGO      = 'pago',      'Pago'
    CANCELADA = 'cancelada', 'Cancelada'
