from itertools import count
from time import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg

import json

from .models import Categoria, Produto, Cliente, Venda, ItemVenda

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('pos')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def pos_view(request):
    categorias = Categoria.objects.filter(ativo=True).prefetch_related('produtos')
    produtos = Produto.objects.filter(ativo=True).select_related('categoria')
    
    context = {
        'categorias': categorias,
        'produtos': produtos,
    }
    return render(request, 'pos.html', context)

@login_required
@require_POST
def buscar_cliente(request):
    termo = request.POST.get("termo", "").strip()

    if not termo:
        return JsonResponse(
            {"success": False, "error": "Informe o nome ou código do cartão"},
            status=400
        )

    clientes = (
        Cliente.objects
        .filter(ativo=True)
        .filter(
            Q(codigo_cartao__iexact=termo) |
            Q(nome__icontains=termo)
        )
        .order_by("nome")[:10]   # hard limit (important for POS)
    )

    if not clientes.exists():
        return JsonResponse(
            {"success": False, "error": "Cliente não encontrado"},
            status=404
        )

    return JsonResponse({
        "success": True,
        "clientes": [
            {
                "id": c.id,
                "nome": c.nome,
                "codigo_cartao": c.codigo_cartao,
            }
            for c in clientes
        ]
    })
    
@login_required
@require_POST
def finalizar_venda(request):
    """Finaliza a venda e registra no banco"""
    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
        itens = data.get('itens', [])
        
        if not cliente_id or not itens:
            return JsonResponse({'error': 'Dados incompletos'}, status=400)
        
        cliente = get_object_or_404(Cliente, id=cliente_id, ativo=True)
        
        with transaction.atomic():
            # Calcula total
            total = Decimal('0.00')
            itens_validados = []
            
            for item in itens:
                produto = get_object_or_404(Produto, id=item['id'], ativo=True)
                quantidade = int(item['quantity'])
                preco = Decimal(str(produto.preco))
                subtotal = preco * quantidade
                
                total += subtotal
                itens_validados.append({
                    'produto': produto,
                    'quantidade': quantidade,
                    'preco_unitario': preco,
                    'subtotal': subtotal
                })
            
            forma = data['forma_pagamento']

            venda = Venda.objects.create(
                cliente=cliente,
                operador=request.user,
                total=total,
                forma_pagamento=forma,
                paga=(forma != 'FIA'),
                quitada_em=None if forma == 'FIA' else timezone.now()
            )

            
            # Cria os itens
            for item in itens_validados:
                ItemVenda.objects.create(
                    venda=venda,
                    produto=item['produto'],
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco_unitario'],
                    subtotal=item['subtotal']
                )
            
            return JsonResponse({
                'success': True,
                'venda_id': venda.id,
                'total': float(total),
                'message': f'Venda #{venda.id} finalizada com sucesso!'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def produtos_list(request):
    produtos = (
        Produto.objects
        .filter(ativo=True)
        .select_related('categoria')
    )

    categorias = (
        Categoria.objects
        .filter(ativo=True)
        .prefetch_related('produtos')
    )

    vendas = (
        Venda.objects
        .select_related('cliente', 'operador')
        .order_by('-data_hora')[:10]
    )

    vendas_stats = Venda.objects.aggregate(
    qtd_vendas=Count('id'),
    faturamento=Sum('total')
)

    return render(
        request,
        'produtos.html',
        {
            'produtos': produtos,
            'categorias': categorias,
            'vendas': vendas,
            'vendas_stats': vendas_stats,
        }
    )
    
@login_required
def vendas_dashboard(request):
    hoje = timezone.now()
    inicio_30d = hoje - timedelta(days=30)

    # -------- KPIs --------
    total_a_receber = (
        Venda.objects
        .filter(paga=False)
        .aggregate(total=Sum('total'))
        ['total'] or 0
    )

    vendas_30d = Venda.objects.filter(data_hora__gte=inicio_30d)

    faturamento_30d = (
        vendas_30d
        .filter(paga=True)
        .aggregate(total=Sum('total'))
        ['total'] or 0
    )

    qtd_vendas_30d = vendas_30d.count()

    ticket_medio_30d = (
        vendas_30d
        .aggregate(media=Avg('total'))
        ['media'] or 0
    )

    # -------- Listagem --------
    vendas = (
        Venda.objects
        .select_related('cliente', 'operador')
        .order_by('-data_hora')[:30]
    )

    return render(
        request,
        'vendas.html',
        {
            'total_a_receber': total_a_receber,
            'faturamento_30d': faturamento_30d,
            'qtd_vendas_30d': qtd_vendas_30d,
            'ticket_medio_30d': ticket_medio_30d,
            'vendas': vendas,
        }
    )
