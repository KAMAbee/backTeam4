"""
Legacy compatibility layer.

Business logic moved to `suppliers`.
"""

from suppliers.views import ContractViewSet, budget_summary

__all__ = ["ContractViewSet", "budget_summary"]