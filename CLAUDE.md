# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cantina is a Django POS (Point of Sale) system for a school cafeteria. It handles product sales, customer management (including credit/fiado accounts), inventory tracking, and sales reporting.

## Common Commands

All Django management commands run from the `cantina/` subdirectory (where `manage.py` lives):

```bash
# Local development (SQLite)
cd cantina
python manage.py runserver          # http://localhost:8000
python manage.py migrate
python manage.py createsuperuser

# Tests
python manage.py test core          # Run all tests
python manage.py test core.tests.TestClassName  # Run a single test class

# Docker (Postgres, port 9000)
docker compose build
docker compose up -d
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test core
```

Environment: copy `.env.example` to `.env`. The app reads `DATABASE_URL` for Postgres or falls back to SQLite.

## Architecture

Single Django app (`core`) with no frontend framework — server-rendered HTML templates with inline JavaScript for the POS interface.

**URL structure:**
- `/` — login
- `/pos/` — cashier POS interface (authenticated)
- `/produtos/`, `/vendas/`, `/estoque/` — admin-only dashboards (superuser)
- `/vendas/?mes=&ano=` — vendas dashboard, scoped to a month (defaults to current)
- `/vendas/lancamento/` — bulk monthly sale entry (admin; no stock decrement, custom date)
- `/vendas/fatura/<id>/<ano>/<mes>/` — download per-client fiado fatura as XLSX (admin)
- `/vendas/<id>/quitar/` — mark a single fiado sale as paid
- `/clientes/<id>/quitar-fiados/` — POST with `mes`/`ano` to quitar all fiados for a client in a given month
- `/vendas/export.csv` — full CSV export
- `/relatorio/mensal/` — monthly report dashboard with product breakdown and SERVICOS distinction (admin)
- `/relatorio/mensal.xlsx` — XLSX export of the monthly report (`?mes=&ano=`)
- `/api/buscar-cliente/` — JSON: search customer by name or card code
- `/api/finalizar-venda/` — JSON: finalize a sale with items, discount, and payment method

**Access control:** `@login_required` for authenticated pages; `@admin_required` (custom decorator, checks `request.user.is_superuser`) for admin-only views.

## Key Models

- **Produto** — has `estoque` field; `estoque = 0` means no inventory tracking. Stock is decremented on sale only when `estoque > 0`. Has `produto_estoque` (FK to self) and `fator_estoque` for linked stock consumption (e.g. pizza slices). `custo` tracks weighted average cost, updated on stock entry.
- **Categoria** — products belong to a category. The `servicos` slug (category "SERVIÇOS") is special: products in it appear in the monthly report but are excluded from Lucro Cantina (they have a separate subtotal row).
- **Venda** — links to `Cliente` (nullable for walk-in), `operador` (User), and holds `subtotal`, `desconto_percentual`, `desconto_valor`, `total`. Payment: `DIN` (cash), `CAR` (card), `PIX`, `FIA` (fiado/credit). `data_hora` defaults to `timezone.now` but can be set explicitly (used by bulk monthly entry).
- **ItemVenda** — sale line items; `preco_unitario` is copied from product at sale time.
- **MovimentacaoEstoque** — manual stock adjustments with `ENT` (entry) or `PER` (loss) types. `custo_unitario` on ENT entries updates the product's weighted average cost.

## Business Rules

- Discount: 0–50% only.
- Credit sales (`FIA`): require an identified customer (`cliente` must be set).
- Stock check: if `produto.estoque > 0`, reject sale if stock is insufficient; decrement on finalize.
- `finalizar_venda` runs inside `@transaction.atomic()` with `select_for_update()` on products to prevent race conditions.
- **Bulk monthly entry** (`/vendas/lancamento/`): creates a `Venda` with a custom `data_hora` (date chosen by admin, time set to noon). Does NOT decrement stock — intended for historical/end-of-month reconciliation. Only DIN/CAR/PIX allowed (no FIA).
- **Faturas**: a "fatura" is a conceptual grouping of `Venda` records with `forma_pagamento='FIA'` for a given client × month. No separate model — just a filtered view + XLSX export. Quitar is scoped to client + month via `mes`/`ano` POST params.
- **Monthly report**: `_build_relatorio_rows(ano, mes)` is a shared helper used by both the dashboard view and the XLSX export. It separates SERVICOS (by `categoria__slug == 'servicos'`) from Cantina products for independent profit subtotals.

## API Response Convention

All `/api/` endpoints return JSON:
```json
{ "success": true }
{ "success": false, "error": "reason" }
```

## Deployment Workflow (MANDATORY after every approved change)

After completing any code change, you MUST follow this exact workflow — no exceptions:

### Step 1 — Safety check (both must be true before proceeding)
1. **No DB impact**: the change must not drop tables, remove columns, alter existing data, or require destructive migrations. Pure template/JS/CSS changes are always safe. New additive migrations (add column with default, add table) are safe. Never run `migrate --fake`, `flush`, `sqlflush`, or delete migration files.
2. **No breaking change**: existing functionality must still work for all users after the deploy.

If either check fails, stop and discuss with the user before proceeding.

### Step 2 — Commit and push
```bash
cd C:/Users/joaov/Desktop/building/cantina
git add -A
git commit -m "<concise description of change>"   # NO co-author line
git push
```

### Step 3 — Deploy to production (Oracle VM)
```bash
ssh -i ~/.ssh/cantina.key ubuntu@40.233.127.51 "cd /opt/cantina/cantina && git pull && docker compose up -d --build"
```

If there are **new migration files** in the commit:
```bash
ssh -i ~/.ssh/cantina.key ubuntu@40.233.127.51 "cd /opt/cantina/cantina && git pull && docker compose up -d --build && docker compose exec web python manage.py migrate"
```

### Step 4 — Verify
After the SSH command returns, confirm the containers are healthy:
```bash
ssh -i ~/.ssh/cantina.key ubuntu@40.233.127.51 "cd /opt/cantina/cantina && docker compose ps"
```

### Key reminders
- **NEVER** run `docker compose down -v`, `manage.py flush`, or any command that wipes volumes/data.
- **NEVER** add `--no-verify` to bypass git hooks.
- `docker compose up -d --build` restarts containers with new code but preserves the Postgres volume.
- The live URL is `http://40.233.127.51`.
