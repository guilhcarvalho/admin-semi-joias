from django.core.validators import RegexValidator


name_validator = RegexValidator(
    regex=r'^[a-zA-ZÀ-ÿ]+$',
    message="Insira um nome válido."
)

phone_validator = RegexValidator(
    regex=r'^\d{11}$',
    message="Insira um número de telefone válido."
)