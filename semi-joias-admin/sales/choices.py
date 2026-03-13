from django.db import models

PAYMENT_METHODS = models.TextChoices(
    "PAYMENT_METHODS",
    [
        ("pix", "Pix"),
        ("debito", "Débito"),
        ("credito", "Crédito"),
        ("dinheiro", "Dinheiro")
    ]
)

PAYMENT_SITUATION = models.TextChoices(
    "PAYMENT_SITUATION",
    [
        ("adimplente", "Adimplente"),
        ("inadimplente", "inadimplente")
    ]
)

MONTH_SELECTION = models.TextChoices(
    "MONTH_SELECTION",
    [
        ("janeiro", "Janeiro"),
        ("fevereiro", "Fevereiro"),
        ("março", "Março"),
        ("abril", "Abril"),
        ("maio", "Maio"),
        ("junho", "Junho"),
        ("julho", "Julho"),
        ("agosto", "Agosto"),
        ("setembro", "Setembro"),
        ("outubro", "Outubro"),
        ("novembro", "Novembro"),
        ("dezembro", "Dezembro")
    ]
)