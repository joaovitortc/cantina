import csv
import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Categoria, Cliente, ItemVenda, MovimentacaoEstoque, Produto, Venda

MAX_DESCONTO_PERCENTUAL = Decimal('50.00')
FORMAS_PAGAMENTO_VALIDAS = {codigo for codigo, _ in Venda.FORMA_PAGAMENTO_CHOICES}


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


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
        .order_by("nome")[:10]
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
    """Finaliza a venda com validações de entrada, desconto e estoque."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    cliente_id = data.get('cliente_id')
    itens = data.get('itens', [])
    forma = data.get('forma_pagamento')

    if not itens:
        return JsonResponse({'success': False, 'error': 'Dados incompletos'}, status=400)

    if forma not in FORMAS_PAGAMENTO_VALIDAS:
        return JsonResponse({'success': False, 'error': 'Forma de pagamento inválida'}, status=400)

    try:
        desconto_percentual = Decimal(str(data.get('desconto_percentual', 0)))
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Desconto inválido'}, status=400)

    if desconto_percentual < 0 or desconto_percentual > MAX_DESCONTO_PERCENTUAL:
        return JsonResponse({'success': False, 'error': 'Desconto deve estar entre 0% e 50%'}, status=400)

    cliente = None
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id, ativo=True)

    if forma == 'FIA' and not cliente:
        return JsonResponse({'success': False, 'error': 'Fiado só é permitido para cliente identificado'}, status=400)

    try:
        with transaction.atomic():
            subtotal = Decimal('0.00')
            itens_validados = []

            for item in itens:
                produto_id = item.get('id')
                quantidade_raw = item.get('quantity')

                if produto_id is None or quantidade_raw is None:
                    return JsonResponse({'success': False, 'error': 'Item inválido na venda'}, status=400)

                try:
                    quantidade = int(quantidade_raw)
                except (TypeError, ValueError):
                    return JsonResponse({'success': False, 'error': 'Quantidade inválida'}, status=400)

                if quantidade <= 0:
                    return JsonResponse({'success': False, 'error': 'Quantidade deve ser maior que zero'}, status=400)

                produto = get_object_or_404(Produto.objects.select_for_update(), id=produto_id, ativo=True)

                if produto.estoque > 0 and quantidade > produto.estoque:
                    return JsonResponse(
                        {'success': False, 'error': f'Estoque insuficiente para {produto.nome}'},
                        status=400
                    )

                preco = Decimal(str(produto.preco))
                subtotal_item = preco * quantidade
                subtotal += subtotal_item

                itens_validados.append({
                    'produto': produto,
                    'quantidade': quantidade,
                    'preco_unitario': preco,
                    'subtotal': subtotal_item,
                })

            desconto_valor = (subtotal * desconto_percentual) / Decimal('100')
            total = subtotal - desconto_valor

            venda = Venda.objects.create(
                cliente=cliente,
                operador=request.user,
                subtotal=subtotal,
                desconto_percentual=desconto_percentual,
                desconto_valor=desconto_valor,
                total=total,
                forma_pagamento=forma,
                paga=(forma != 'FIA'),
                quitada_em=None if forma == 'FIA' else timezone.now(),
            )

            for item in itens_validados:
                produto = item['produto']

                if produto.estoque > 0:
                    produto.estoque -= item['quantidade']
                    produto.save(update_fields=['estoque'])

                ItemVenda.objects.create(
                    venda=venda,
                    produto=produto,
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco_unitario'],
                    subtotal=item['subtotal'],
                )

            return JsonResponse({
                'success': True,
                'venda_id': venda.id,
                'subtotal': float(subtotal),
                'desconto_percentual': float(desconto_percentual),
                'desconto_valor': float(desconto_valor),
                'total': float(total),
                'message': f'Venda #{venda.id} finalizada com sucesso!',
            })

    except Exception:
        return JsonResponse({'success': False, 'error': 'Erro interno ao finalizar venda'}, status=500)


@login_required
@admin_required
def produtos_list(request):
    termo = request.GET.get('q', '').strip()
    categoria_slug = request.GET.get('categoria', '').strip()

    produtos = Produto.objects.filter(ativo=True).select_related('categoria')

    if termo:
        produtos = produtos.filter(nome__icontains=termo)

    if categoria_slug:
        produtos = produtos.filter(categoria__slug=categoria_slug)

    categorias = Categoria.objects.filter(ativo=True).prefetch_related('produtos')

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
            'filtro_q': termo,
            'filtro_categoria': categoria_slug,
        }
    )


@login_required
@admin_required
def vendas_dashboard(request):
    hoje = timezone.now()
    inicio_30d = hoje - timedelta(days=30)

    total_a_receber = (
        Venda.objects
        .filter(paga=False)
        .aggregate(total=Sum('total'))
        ['total'] or 0
    )

    vendas_30d = Venda.objects.filter(data_hora__gte=inicio_30d)

    faturamento_30d = (
        vendas_30d
        .aggregate(total=Sum('total'))
        ['total'] or 0
    )

    qtd_vendas_30d = vendas_30d.count()

    ticket_medio_30d = (
        vendas_30d
        .aggregate(media=Avg('total'))
        ['media'] or 0
    )

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


@login_required
@admin_required
@require_POST
def quitar_venda(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)

    if venda.paga:
        messages.info(request, f'Venda #{venda.id} já está quitada.')
        return redirect('vendas')

    venda.paga = True
    venda.quitada_em = timezone.now()
    venda.save(update_fields=['paga', 'quitada_em'])

    messages.success(request, f'Venda #{venda.id} quitada com sucesso.')
    return redirect('vendas')


@login_required
@admin_required
def exportar_vendas_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendas.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Data', 'Cliente', 'Operador', 'Forma de pagamento',
        'Subtotal', 'Desconto (%)', 'Desconto (R$)', 'Total', 'Status'
    ])

    for venda in Venda.objects.select_related('cliente', 'operador').order_by('-data_hora'):
        writer.writerow([
            venda.id,
            venda.data_hora.strftime('%d/%m/%Y %H:%M'),
            venda.cliente.nome if venda.cliente else 'Consumidor final',
            venda.operador.username if venda.operador else '-',
            venda.get_forma_pagamento_display().replace('Cartão', 'Cartao'),
            venda.subtotal,
            venda.desconto_percentual,
            venda.desconto_valor,
            venda.total,
            'Paga' if venda.paga else 'Fiado',
        ])

    return response


@login_required
@admin_required
def estoque_view(request):
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        tipo = request.POST.get('tipo')
        motivo = request.POST.get('motivo', '').strip()

        try:
            quantidade = int(request.POST.get('quantidade', '0'))
        except ValueError:
            messages.error(request, 'Quantidade inválida.')
            return redirect('estoque')

        if tipo not in {'ENT', 'PER'}:
            messages.error(request, 'Tipo de movimentação inválido.')
            return redirect('estoque')

        if quantidade <= 0:
            messages.error(request, 'A quantidade deve ser maior que zero.')
            return redirect('estoque')

        produto = get_object_or_404(Produto, id=produto_id)

        with transaction.atomic():
            produto = Produto.objects.select_for_update().get(id=produto.id)

            if tipo == 'PER' and quantidade > produto.estoque:
                messages.error(request, f'Estoque insuficiente para perda de {produto.nome}.')
                return redirect('estoque')

            if tipo == 'ENT':
                produto.estoque += quantidade
            else:
                produto.estoque -= quantidade

            produto.save(update_fields=['estoque'])

            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo=tipo,
                quantidade=quantidade,
                motivo=motivo,
                usuario=request.user,
            )

        messages.success(request, 'Movimentação de estoque registrada com sucesso.')
        return redirect('estoque')

    produtos = Produto.objects.filter(ativo=True).select_related('categoria').order_by('nome')
    movimentacoes = MovimentacaoEstoque.objects.select_related('produto', 'usuario')[:40]

    return render(
        request,
        'estoque.html',
        {
            'produtos': produtos,
            'movimentacoes': movimentacoes,
        }
    )
