from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0012_itensvenda_unique_sale_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parcela',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(verbose_name='número')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='valor')),
                ('situacao', models.CharField(
                    choices=[('pendente', 'Pendente'), ('pago', 'Pago')],
                    default='pendente',
                    max_length=10,
                    verbose_name='situação',
                )),
                ('venda', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='parcelas',
                    to='sales.vendas',
                    verbose_name='venda',
                )),
            ],
            options={
                'verbose_name': 'parcela',
                'verbose_name_plural': 'parcelas',
                'ordering': ['numero'],
                'unique_together': {('venda', 'numero')},
            },
        ),
    ]
