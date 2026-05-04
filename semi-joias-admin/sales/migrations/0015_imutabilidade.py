from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0014_fix_choices_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendas',
            name='status',
            field=models.CharField(
                choices=[('ativa', 'Ativa'), ('cancelada', 'Cancelada'), ('devolvida_parcial', 'Devolução Parcial')],
                default='ativa',
                max_length=20,
                verbose_name='status',
            ),
        ),
        migrations.AlterField(
            model_name='parcela',
            name='situacao',
            field=models.CharField(
                choices=[('pendente', 'Pendente'), ('pago', 'Pago'), ('cancelada', 'Cancelada')],
                default='pendente',
                max_length=10,
                verbose_name='situação',
            ),
        ),
        migrations.CreateModel(
            name='Devolucao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.TextField(blank=True, verbose_name='motivo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='data')),
                ('venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devolucoes', to='sales.vendas', verbose_name='venda')),
            ],
            options={
                'verbose_name': 'devolução',
                'verbose_name_plural': 'devoluções',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ItemDevolucao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.PositiveIntegerField(verbose_name='quantidade')),
                ('valor_estornado', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='valor estornado')),
                ('devolucao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='sales.devolucao', verbose_name='devolução')),
                ('item_venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devolucoes', to='sales.itensvenda', verbose_name='item da venda')),
            ],
            options={
                'verbose_name': 'item da devolução',
                'verbose_name_plural': 'itens da devolução',
            },
        ),
        migrations.CreateModel(
            name='Garantia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.PositiveIntegerField(verbose_name='quantidade')),
                ('motivo', models.TextField(verbose_name='motivo')),
                ('status', models.CharField(
                    choices=[('enviado', 'Enviado'), ('em_analise', 'Em Análise'), ('resolvido', 'Resolvido'), ('recusado', 'Recusado')],
                    default='enviado',
                    max_length=10,
                    verbose_name='status',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='data de envio')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualização')),
                ('item_venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='garantias', to='sales.itensvenda', verbose_name='item da venda')),
            ],
            options={
                'verbose_name': 'garantia',
                'verbose_name_plural': 'garantias',
                'ordering': ['-created_at'],
            },
        ),
    ]
