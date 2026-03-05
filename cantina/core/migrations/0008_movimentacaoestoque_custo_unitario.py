from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_produto_estoque_fator'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimentacaoestoque',
            name='custo_unitario',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Custo por unidade pago nesta entrada (usado para calcular custo médio)',
                max_digits=10,
                null=True,
                verbose_name='Custo unitário',
            ),
        ),
    ]
