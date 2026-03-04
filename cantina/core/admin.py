from django.contrib import admin

from .models import Categoria, Cliente, ItemVenda, MovimentacaoEstoque, Produto, Venda


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'ativo', 'ordem']
    list_filter = ['ativo']
    search_fields = ['nome']
    prepopulated_fields = {'slug': ('nome',)}


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "preco", "custo", "estoque", "fator_estoque", "produto_estoque", "ativo")
    list_editable = ("preco", "custo", "estoque", "ativo")
    search_fields = ("nome",)
    fieldsets = (
        (None, {
            'fields': ('nome', 'categoria', 'descricao', 'preco', 'custo', 'ativo'),
        }),
        ('Estoque', {
            'fields': ('estoque',),
        }),
        ('Vínculo de estoque (ex: fatias de pizza)', {
            'fields': ('produto_estoque', 'fator_estoque'),
            'description': (
                'Use quando este produto consome o estoque de outro produto. '
                'Ex: "Pizza Fatia" → Produto de estoque: Pizza, Fator: 1. '
                'Para produtos que consomem múltiplas unidades do próprio estoque '
                '(ex: Pizza Inteira = 6 fatias), deixe Produto de estoque em branco '
                'e defina o Fator aqui.'
            ),
        }),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo_cartao', 'telefone', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'codigo_cartao']


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'operador', 'data_hora', 'subtotal', 'desconto_percentual', 'desconto_valor', 'total', 'paga']
    list_filter = ['data_hora', 'paga', 'forma_pagamento']
    search_fields = ['cliente__nome']
    readonly_fields = ['data_hora', 'subtotal', 'desconto_percentual', 'desconto_valor', 'total']
    inlines = [ItemVendaInline]


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['criado_em', 'produto', 'tipo', 'quantidade', 'usuario']
    list_filter = ['tipo', 'criado_em']
    search_fields = ['produto__nome', 'motivo']
