from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # path("health/", views.health, name="health"),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pos/', views.pos_view, name='pos'),
    path('produtos/', views.produtos_list, name='produtos_list'),
    path('api/buscar-cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('api/finalizar-venda/', views.finalizar_venda, name='finalizar_venda'),
    path('vendas/', views.vendas_dashboard, name='vendas'),

]
