import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Cliente, Produto, Venda


class POSFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='op', password='123456')
        self.client.login(username='op', password='123456')

        self.categoria = Categoria.objects.create(nome='Bebidas', slug='bebidas')
        self.cliente = Cliente.objects.create(nome='Aluno 1', codigo_cartao='ABC123')
        self.produto = Produto.objects.create(
            nome='Suco',
            categoria=self.categoria,
            custo=Decimal('2.50'),
            preco=Decimal('5.00'),
            estoque=10,
            ativo=True,
        )

    def test_buscar_cliente_por_nome(self):
        response = self.client.post(reverse('buscar_cliente'), {'termo': 'Aluno'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_finalizar_venda_com_desconto_e_estoque(self):
        payload = {
            'cliente_id': self.cliente.id,
            'forma_pagamento': 'DIN',
            'desconto_percentual': 10,
            'itens': [
                {'id': self.produto.id, 'quantity': 2},
            ],
        }

        response = self.client.post(
            reverse('finalizar_venda'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.produto.refresh_from_db()
        venda = Venda.objects.get()

        self.assertEqual(self.produto.estoque, 8)
        self.assertEqual(venda.subtotal, Decimal('10.00'))
        self.assertEqual(venda.desconto_percentual, Decimal('10'))
        self.assertEqual(venda.total, Decimal('9.00'))

    def test_finalizar_venda_rejeita_desconto_acima_de_50(self):
        payload = {
            'cliente_id': self.cliente.id,
            'forma_pagamento': 'DIN',
            'desconto_percentual': 60,
            'itens': [
                {'id': self.produto.id, 'quantity': 1},
            ],
        }

        response = self.client.post(
            reverse('finalizar_venda'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)

    def test_finalizar_venda_rejeita_quantidade_invalida(self):
        payload = {
            'cliente_id': self.cliente.id,
            'forma_pagamento': 'DIN',
            'desconto_percentual': 0,
            'itens': [
                {'id': self.produto.id, 'quantity': 0},
            ],
        }

        response = self.client.post(
            reverse('finalizar_venda'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
