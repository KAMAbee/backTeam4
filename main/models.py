"""
`main` is now a legacy app.

Models were moved into domain apps:
- `accounts`: User / Organization / Department
- `trainings`: Training / TrainingSession
- `suppliers`: Supplier / Contract / ContractAllocation

This module re-exports models for backwards compatibility only.
Prefer importing from the domain apps directly.
"""

from accounts.models import Department, Organization, User
from suppliers.models import Contract, ContractAllocation, Supplier
from trainings.models import Training, TrainingSession

__all__ = [
    "User",
    "Organization",
    "Department",
    "Supplier",
    "Contract",
    "ContractAllocation",
    "Training",
    "TrainingSession",
]