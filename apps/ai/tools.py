"""
Tool functions intended for a future LLM-backed AI Financial Agent.

None of these are wired to an actual LLM yet. When that integration
is added, the model must call these functions as *tools* and treat
their return values as ground truth -- the LLM is never the source
of truth for balances, transactions, or calculations (see
apps.finance.engine, which is what all of these wrap).
"""

from apps.finance import engine


def get_financial_summary(user):
    return engine.build_financial_summary(user)


def get_expense_breakdown(user):
    return engine.get_expense_breakdown(user)


def get_income(user):
    return engine.get_monthly_income(user)


def get_debt(user):
    return engine.get_total_debt(user)


def calculate_investable_capital(user):
    return engine.calculate_investable_capital(user)
