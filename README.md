# FinAI — Personal AI CFO / Financial OS (Foundation)

This is the two-week MVP foundation for FinAI: a secure Django product
skeleton with authentication, a light-theme navy/gold dashboard, a
deterministic financial calculation engine, and an abstraction layer
for future provider integrations. **No real banking, trading, or money
movement is implemented.** Everything financial you see is demo data.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit DJANGO_SECRET_KEY etc.
python manage.py migrate
python manage.py seed_demo_data          # creates demo@finai.app / DemoUser-2026!
python manage.py runserver
```

The application database is PostgreSQL. Configure `POSTGRES_DB`,
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`
in `.env` before running migrations.

For a persistent local database, run `docker compose up -d postgres`, then
run `python manage.py migrate`. The compose service uses a named volume and
does not expose SQLite as an application database.

Visit `http://127.0.0.1:8000/`. Log in with the seeded demo account,
or register a new one.

Reset demo data at any time:

```bash
python manage.py seed_demo_data --reset
```

Run tests:

```bash
python manage.py test apps
```

## What's implemented

- **Auth** (`apps/accounts`): email-or-phone registration/login/logout,
  Argon2 password hashing, rate-limited login/register, generic error
  messages (no account enumeration), session rotation on login,
  password-reset token flow, and email OTP verification with hashed codes,
  five-attempt limits, and three-minute lockouts. Phone OTP remains an
  architecture placeholder (`PhoneOTP` in `apps/accounts/models.py`).
- **Financial data model** (`apps/finance/models.py`): FinancialAccount,
  Transaction, Income, Asset, Liability, Installment, Goal,
  RiskProfile, Portfolio, Holding.
- **Deterministic financial engine** (`apps/finance/engine.py`): net
  worth, cash/investment/debt totals, savings rate, allocation,
  investable capital (cash minus emergency reserve minus near-term
  goal gaps minus debt — not a naive "leftover cash" rule). Fully
  unit tested in `apps/finance/tests.py`, including cross-user data
  isolation.
- **Provider abstraction** (`apps/integrations/providers.py`):
  `BankProvider`, `CryptoProvider`, `GoldProvider`, `SilverProvider`,
  `InvestmentProvider`, `ShoppingProvider`, `CreditProvider`,
  `MarketDataProvider` interfaces. No concrete implementations exist
  yet (Nobitex, Digikala, etc. are not connected).
- **AI tool layer** (`apps/ai/tools.py`): thin wrapper functions a
  future LLM agent would call as *tools* — they all delegate to the
  deterministic engine. No LLM is wired up.
- **Personality** (`apps/personality`): MBTI-style assessment models,
  kept explicitly separate from the deterministic `RiskProfile`.
- **Expenses** (`apps/expenses`): category breakdown, month-over-month
  comparison, recent transactions — all computed from real demo
  transaction rows.
- **UI**: Persian-first RTL light theme using the exact brand palette
  (`#000814`, `#001D3D`, `#003566`, `#CCA000`, `#F0CB46`), responsive
  navigation, and public About, Services, Support, and Contact pages.
  Unbuilt integrations use clear "به‌زودی" states instead of broken links.
- **Security**: secure cookies, CSRF, argon2 hashing, HSTS when
  `DEBUG=False`, no secrets in git (`.env` is gitignored), rate
  limiting on auth endpoints, object-level ownership on every finance
  model (`UserOwnedModel`), audit-log foundation (`apps/ai/models.py`).

## What's intentionally NOT implemented

- Real bank/crypto/gold/stock/shopping/BNPL integrations (interfaces
  only — see `apps/integrations/providers.py`)
- SMS OTP delivery (architecture only)
- Autonomous or manual trade execution
- Real money transfer
- LLM integration (tool functions exist and are ready to be called by
  one, per `apps/ai/tools.py`)

## Project layout

```
apps/
  accounts/      auth, users, tokens
  core/          landing, dashboard, daily quote, coming-soon, seed command
  finance/       models + deterministic engine (the source of truth)
  expenses/      expense views built on the finance engine
  personality/   MBTI-style assessments (separate from RiskProfile)
  goals/         placeholder for the future deterministic Goal Engine
  risk/          placeholder for the future deterministic Risk Engine
  investments/   placeholder for portfolio-specific views
  reports/       placeholder
  ai/            tool functions + conversation/recommendation/audit models
  integrations/  provider abstraction layer + ProviderConnection model
  quant/         placeholder for future LEAN/backtesting integration
config/          settings, urls, wsgi/asgi
templates/       base + per-app templates
static/css/      design system (main.css)
```

## Next steps (not in this session)

- Wire a real cache backend (Redis) for rate limiting in production
- Add DRF and expose `/api/...` endpoints per the future API architecture
- Build the Goal Engine and Risk Engine as their own service modules
  (currently the models exist in `apps/finance`, but the calculation
  logic beyond `calculate_investable_capital` is not yet built out)
- Persian (`fa`) translation strings via Django's i18n `{% trans %}`
- CI running `manage.py test` on push
