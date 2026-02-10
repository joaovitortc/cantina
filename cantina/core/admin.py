from django.contrib import admin
from .models import Categoria, Produto, Cliente, Venda, ItemVenda

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'ativo', 'ordem']
    list_filter = ['ativo']
    search_fields = ['nome']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "preco", "custo", "estoque", "ativo")
    list_editable = ("preco", "custo", "estoque", "ativo")
    search_fields = ("nome",)

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
    list_display = ['id', 'cliente', 'operador', 'data_hora', 'total']
    list_filter = ['data_hora']
    search_fields = ['cliente__nome']
    readonly_fields = ['data_hora', 'total']
    inlines = [ItemVendaInline]