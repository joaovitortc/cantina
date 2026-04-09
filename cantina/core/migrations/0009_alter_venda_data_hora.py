import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_movimentacaoestoque_custo_unitario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venda',
            name='data_hora',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
