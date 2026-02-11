from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_venda_options_venda_forma_pagamento_venda_paga_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='venda',
            name='desconto_percentual',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='venda',
            name='desconto_valor',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='venda',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.CreateModel(
            name='MovimentacaoEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('ENT', 'Entrada'), ('PER', 'Perda')], max_length=3)),
                ('quantidade', models.PositiveIntegerField()),
                ('motivo', models.CharField(blank=True, max_length=255)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes_estoque', to='core.produto')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={
                'verbose_name': 'Movimentação de Estoque',
                'verbose_name_plural': 'Movimentações de Estoque',
                'ordering': ['-criado_em'],
            },
        ),
    ]
