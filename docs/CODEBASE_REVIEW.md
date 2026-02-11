# Cantina Codebase Review

## High-level architecture

- Framework: Django project (`cantina`) with a single app (`core`).
- Data layer: SQLite (`db.sqlite3`) with models for categories, products, customers, sales, and sale items.
- UI layer: server-rendered Django templates (`login`, `pos`, `produtos`, `vendas`) styled with utility classes.
- API layer: lightweight JSON endpoints for customer search and sale checkout under `/api/`.

## Main flows

1. **Authentication**
   - Root route (`/`) renders login form and authenticates users.
2. **POS sales flow**
   - `/pos/` shows active categories and products.
   - `/api/buscar-cliente/` resolves a customer by card code or partial name.
   - `/api/finalizar-venda/` persists a sale and its items in one transaction.
3. **Backoffice**
   - `/produtos/` lists products/categories and shows recent sales summary.
   - `/vendas/` shows KPI cards and recent sales table.

## Potential issues spotted

### 1) Broad exception handling in checkout API
`finalizar_venda` catches all exceptions and returns raw exception text in the response. This may leak internal details and makes debugging/monitoring inconsistent.

### 2) Missing validation of item quantities and payment code
The sale endpoint parses quantity as `int(item['quantity'])` but does not reject zero/negative values and does not explicitly validate `forma_pagamento` before persisting.

### 3) Inventory (`estoque`) is never updated
`Produto.estoque` exists, but checkout does not decrement stock, so stored inventory drifts from reality if stock control is intended.

### 4) Unused/incorrect imports in views
`from itertools import count`, `from time import timezone`, and `authenticate` are imported but not used. `timezone` from `time` is overshadowed by Django timezone import, which is noisy and confusing.

### 5) No automated tests
`core/tests.py` is still the default placeholder. Regressions in POS endpoints and KPIs are likely to slip in unnoticed.

### 6) Production safety defaults
Settings currently include a hardcoded dev secret key, `DEBUG = True`, and empty `ALLOWED_HOSTS`, which is risky if deployed as-is.

## Easy features to implement next (high impact, low effort)

1. **Mark fiado sales as paid**
   - Add a simple POST endpoint/button in `/vendas/` to toggle `paga=True` and set `quitada_em=timezone.now()`.
   - Small model/view/template change, immediate operational benefit.

2. **Basic input validation for checkout**
   - Reject non-positive quantities and unknown payment methods with clear 400 responses.
   - Minimal code change and large reliability improvement.

3. **Stock decrement on checkout (when `estoque > 0`)**
   - Inside the existing transaction, decrease stock for controlled items and reject insufficient stock.
   - Uses fields already present in the model.

4. **Search/filter on products page**
   - Add query params for category and product name in `/produtos/`.
   - Fast to build, improves daily usability.

5. **Simple test coverage for core endpoints**
   - Add tests for `buscar_cliente`, successful checkout, and invalid payloads.
   - Good confidence boost with small time investment.

6. **CSV export of sales list**
   - Add `/vendas/export.csv` with date range filter.
   - Straightforward implementation using queryset + `HttpResponse`.

## Suggested implementation order

1. Checkout validations
2. Fiado settlement endpoint
3. Stock decrement logic
4. Product filters
5. Automated tests for all above
6. CSV export
