from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_venda_desconto_movimentacaoestoque'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venda',
            name='cliente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vendas', to='core.cliente'),
        ),
    ]
