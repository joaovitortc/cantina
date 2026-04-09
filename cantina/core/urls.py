from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pos/', views.pos_view, name='pos'),
    path('produtos/', views.produtos_list, name='produtos_list'),
    path('vendas/', views.vendas_dashboard, name='vendas'),
    path('vendas/export.csv', views.exportar_vendas_csv, name='exportar_vendas_csv'),
    path('vendas/export-clientes.csv', views.exportar_vendas_clientes_csv, name='exportar_vendas_clientes_csv'),
    path('vendas/<int:venda_id>/quitar/', views.quitar_venda, name='quitar_venda'),
    path('clientes/<int:cliente_id>/quitar-fiados/', views.quitar_cliente_fiados, name='quitar_cliente_fiados'),
    path('estoque/', views.estoque_view, name='estoque'),

    path('api/buscar-cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('api/finalizar-venda/', views.finalizar_venda, name='finalizar_venda'),

    path('vendas/lancamento/', views.lancar_venda_mensal, name='lancamento_mensal'),
    path('vendas/fatura/<int:cliente_id>/<int:ano>/<int:mes>/', views.baixar_fatura_cliente, name='baixar_fatura_cliente'),
    path('relatorio/mensal/', views.relatorio_mensal_dashboard, name='relatorio_mensal'),
    path('relatorio/mensal.xlsx', views.relatorio_mensal_xlsx, name='relatorio_mensal_xlsx'),
]
