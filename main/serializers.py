"""
Legacy compatibility layer.

Business logic moved to `suppliers`.
"""

from suppliers.serializers import ContractSerializer

__all__ = ["ContractSerializer"]