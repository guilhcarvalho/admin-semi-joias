from django.db import migrations

PAYMENT_METHOD_MAP = {
    'Pix':      'pix',
    'Débito':   'debito',
    'Crédito':  'credito',
    'Dinheiro': 'dinheiro',
}

SITUATION_MAP = {
    'Adimplente': 'adimplente',
}

MONTH_MAP = {
    'Janeiro':   'janeiro',
    'Fevereiro': 'fevereiro',
    'Março':     'março',
    'Abril':     'abril',
    'Maio':      'maio',
    'Junho':     'junho',
    'Julho':     'julho',
    'Agosto':    'agosto',
    'Setembro':  'setembro',
    'Outubro':   'outubro',
    'Novembro':  'novembro',
    'Dezembro':  'dezembro',
}


def fix_forward(apps, schema_editor):
    Vendas = apps.get_model('sales', 'Vendas')
    Maleta = apps.get_model('sales', 'Maleta')

    for venda in Vendas.objects.all():
        changed = False
        new_pm = PAYMENT_METHOD_MAP.get(venda.payment_method)
        if new_pm:
            venda.payment_method = new_pm
            changed = True
        new_sit = SITUATION_MAP.get(venda.in_good_standing)
        if new_sit:
            venda.in_good_standing = new_sit
            changed = True
        if changed:
            venda.save()

    for maleta in Maleta.objects.all():
        new_month = MONTH_MAP.get(maleta.month)
        if new_month:
            maleta.month = new_month
            maleta.save()


def fix_backward(apps, schema_editor):
    Vendas = apps.get_model('sales', 'Vendas')
    Maleta = apps.get_model('sales', 'Maleta')

    reverse_pm    = {v: k for k, v in PAYMENT_METHOD_MAP.items()}
    reverse_sit   = {v: k for k, v in SITUATION_MAP.items()}
    reverse_month = {v: k for k, v in MONTH_MAP.items()}

    for venda in Vendas.objects.all():
        changed = False
        new_pm = reverse_pm.get(venda.payment_method)
        if new_pm:
            venda.payment_method = new_pm
            changed = True
        new_sit = reverse_sit.get(venda.in_good_standing)
        if new_sit:
            venda.in_good_standing = new_sit
            changed = True
        if changed:
            venda.save()

    for maleta in Maleta.objects.all():
        new_month = reverse_month.get(maleta.month)
        if new_month:
            maleta.month = new_month
            maleta.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0013_parcela'),
    ]

    operations = [
        migrations.RunPython(fix_forward, fix_backward),
    ]
