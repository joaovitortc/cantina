from django.db import models
from django.contrib.auth.models import User


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="produtos"
    )

    custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Custo do produto"
    )

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Preço de venda"
    )

    ativo = models.BooleanField(default=True)

    estoque = models.IntegerField(
        default=0,
        help_text="Deixe 0 para produtos sem controle de estoque"
    )

    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} - Venda: R$ {self.preco} | Custo: R$ {self.custo}"


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    codigo_cartao = models.CharField(max_length=100, unique=True, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Venda(models.Model):
    FORMA_PAGAMENTO_CHOICES = [
        ('DIN', 'Dinheiro'),
        ('CAR', 'Cartão'),
        ('PIX', 'PIX'),
        ('FIA', 'Fiado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='vendas')
    operador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    forma_pagamento = models.CharField(
        max_length=3,
        choices=FORMA_PAGAMENTO_CHOICES
    )

    paga = models.BooleanField(default=True)
    quitada_em = models.DateTimeField(null=True, blank=True)
    observacao = models.TextField(blank=True)

    def __str__(self):
        return f"Venda #{self.id} - {self.cliente.nome}"


class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de Venda'
        verbose_name_plural = 'Itens de Venda'

    def save(self, *args, **kwargs):
        self.subtotal = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('ENT', 'Entrada'),
        ('PER', 'Perda'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='movimentacoes_estoque')
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    motivo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})"
